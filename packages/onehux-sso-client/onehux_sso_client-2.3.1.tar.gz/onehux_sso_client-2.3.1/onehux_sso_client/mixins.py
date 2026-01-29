# onehux_sso_client/mixins.py

"""
Mixins for protecting Class-Based Views with Onehux SSO
"""

from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
import logging

from .utils import SSOSessionManager, OnehuxSSOClient

logger = logging.getLogger(__name__)


# ============================================================================
# CORE SSO AUTHENTICATION MIXIN
# ============================================================================

class SSOLoginRequiredMixin:
    """
    Mixin to ensure user is authenticated via SSO.
    
    Similar to Django's LoginRequiredMixin but for SSO.
    
    Usage:
        class MyProtectedView(SSOLoginRequiredMixin, TemplateView):
            template_name = 'my_template.html'
    """
    
    def dispatch(self, request, *args, **kwargs):
        # CHECK 1: Is user authenticated via Django?
        if not request.user.is_authenticated:
            logger.info(f"User not authenticated, initiating SSO flow for: {request.path}")
            
            # Store the next URL for redirect after login
            request.session['login_next_url'] = request.path
            
            # Initialize SSO client
            client = OnehuxSSOClient()
            
            # Generate authorization URL with prompt='login'
            auth_url, state, code_verifier = client.get_authorization_url(
                request, 
                prompt='login'
            )
            
            return redirect(auth_url)
        
        # CHECK 2: Does user have valid SSO token?
        access_token = SSOSessionManager.get_access_token(request)
        
        if not access_token:
            logger.warning(f"No SSO token for user {request.user.email}, re-authenticating")
            
            request.session['login_next_url'] = request.path
            client = OnehuxSSOClient()
            auth_url, state, code_verifier = client.get_authorization_url(
                request, 
                prompt='login'
            )
            
            return redirect(auth_url)
        
        # CHECK 3: Is token still valid? (Auto-refresh if needed)
        if not SSOSessionManager.refresh_token_if_needed(request):
            logger.warning(f"Token refresh failed for user {request.user.email}, forcing re-login")
            
            request.session['login_next_url'] = request.path
            client = OnehuxSSOClient()
            auth_url, state, code_verifier = client.get_authorization_url(
                request, 
                prompt='login'
            )
            
            return redirect(auth_url)
        
        # All checks passed - proceed with view
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# ROLE-BASED MIXINS
# ============================================================================

class SSORequireRoleMixin:
    """
    Mixin to ensure user has a specific role in current organization.
    
    Attributes:
        required_role (str): The role name required
    
    Usage:
        class AdminView(SSORequireRoleMixin, SSOLoginRequiredMixin, TemplateView):
            required_role = 'admin'
            template_name = 'admin.html'
    """
    
    required_role = None  # Must be set by subclass
    
    def dispatch(self, request, *args, **kwargs):
        if self.required_role is None:
            raise ValueError(
                f"{self.__class__.__name__} must define 'required_role' attribute"
            )
        
        # Get user's roles from session
        user_info = request.session.get('sso_user_info', {})
        user_roles = user_info.get('roles', [])
        
        # Check if user has the required role
        if self.required_role not in user_roles:
            logger.warning(
                f"User {request.user.email} attempted to access {self.__class__.__name__} "
                f"without required role: {self.required_role}"
            )
            
            return render(
                request, 
                'onehux_sso_client/403.html',
                {
                    'required_role': self.required_role,
                    'user_roles': user_roles,
                },
                status=403
            )
        
        # User has required role
        return super().dispatch(request, *args, **kwargs)


class SSORequireAnyRoleMixin:
    """
    Mixin to ensure user has at least one of the specified roles.
    
    Attributes:
        required_roles (list): List of acceptable role names
    
    Usage:
        class ModeratorView(SSORequireAnyRoleMixin, SSOLoginRequiredMixin, ListView):
            required_roles = ['admin', 'moderator', 'editor']
            model = Content
    """
    
    required_roles = None  # Must be set by subclass
    
    def dispatch(self, request, *args, **kwargs):
        if self.required_roles is None:
            raise ValueError(
                f"{self.__class__.__name__} must define 'required_roles' attribute"
            )
        
        # Get user's roles from session
        user_info = request.session.get('sso_user_info', {})
        user_roles = user_info.get('roles', [])
        
        # Check if user has any of the required roles
        has_required_role = any(role in user_roles for role in self.required_roles)
        
        if not has_required_role:
            logger.warning(
                f"User {request.user.email} attempted to access {self.__class__.__name__} "
                f"without any required roles: {self.required_roles}"
            )
            
            return render(
                request, 
                'onehux_sso_client/403.html',
                {
                    'required_roles': self.required_roles,
                    'user_roles': user_roles,
                },
                status=403
            )
        
        return super().dispatch(request, *args, **kwargs)


class SSORequireAllRolesMixin:
    """
    Mixin to ensure user has ALL of the specified roles.
    
    Attributes:
        required_roles (list): List of required role names (must have all)
    
    Usage:
        class AdminDevView(SSORequireAllRolesMixin, SSOLoginRequiredMixin, TemplateView):
            required_roles = ['admin', 'developer']
            template_name = 'admin_dev.html'
    """
    
    required_roles = None  # Must be set by subclass
    
    def dispatch(self, request, *args, **kwargs):
        if self.required_roles is None:
            raise ValueError(
                f"{self.__class__.__name__} must define 'required_roles' attribute"
            )
        
        # Get user's roles from session
        user_info = request.session.get('sso_user_info', {})
        user_roles = user_info.get('roles', [])
        
        # Check if user has all required roles
        has_all_roles = all(role in user_roles for role in self.required_roles)
        
        if not has_all_roles:
            missing_roles = [role for role in self.required_roles if role not in user_roles]
            logger.warning(
                f"User {request.user.email} attempted to access {self.__class__.__name__} "
                f"but missing roles: {missing_roles}"
            )
            
            return render(
                request, 
                'onehux_sso_client/403.html',
                {
                    'required_roles': self.required_roles,
                    'missing_roles': missing_roles,
                    'user_roles': user_roles,
                },
                status=403
            )
        
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# PERMISSION-BASED MIXIN
# ============================================================================

class SSORequirePermissionMixin:
    """
    Mixin to ensure user has a specific permission.
    
    Attributes:
        required_permission (str): The permission name required
    
    Usage:
        class DeletePostView(SSORequirePermissionMixin, SSOLoginRequiredMixin, DeleteView):
            required_permission = 'can_delete_posts'
            model = Post
    """
    
    required_permission = None  # Must be set by subclass
    
    def dispatch(self, request, *args, **kwargs):
        if self.required_permission is None:
            raise ValueError(
                f"{self.__class__.__name__} must define 'required_permission' attribute"
            )
        
        # Get user's permissions from session
        user_info = request.session.get('sso_user_info', {})
        user_permissions = user_info.get('permissions', [])
        
        # Check if user has the required permission
        if self.required_permission not in user_permissions:
            logger.warning(
                f"User {request.user.email} attempted to access {self.__class__.__name__} "
                f"without required permission: {self.required_permission}"
            )
            
            return render(
                request, 
                'onehux_sso_client/403.html',
                {
                    'required_permission': self.required_permission,
                    'user_permissions': user_permissions,
                },
                status=403
            )
        
        return super().dispatch(request, *args, **kwargs)


# ============================================================================
# API-FRIENDLY MIXIN
# ============================================================================

class APISSOLoginRequiredMixin:
    """
    API-friendly version that returns JSON errors instead of redirects.
    
    Usage:
        class APIEndpointView(APISSOLoginRequiredMixin, View):
            def get(self, request):
                return JsonResponse({'data': 'protected'})
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'authentication_required',
                'message': 'You must be logged in to access this endpoint'
            }, status=401)
        
        # Check if SSO token exists
        access_token = SSOSessionManager.get_access_token(request)
        
        if not access_token:
            return JsonResponse({
                'error': 'sso_token_missing',
                'message': 'Valid SSO token required'
            }, status=401)
        
        # Check if token needs refresh
        if not SSOSessionManager.refresh_token_if_needed(request):
            return JsonResponse({
                'error': 'token_refresh_failed',
                'message': 'Unable to refresh authentication token'
            }, status=401)
        
        return super().dispatch(request, *args, **kwargs)
    


