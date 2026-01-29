# Onehux SSO Client for Django

Official Django client library for integrating with [Onehux Accounts](https://accounts.onehux.com) - A production-ready OAuth2/OIDC Identity Provider with SSO/SLO support.

## Features

- ✅ **OAuth2/OIDC Authentication** - Complete authorization code flow with PKCE
- ✅ **Single Sign-On (SSO)** - Seamless login across multiple applications
- ✅ **Single Logout (SLO)** - Logout from all connected applications
- ✅ **Token Management** - Automatic token refresh and validation
- ✅ **User Synchronization** - Real-time user profile updates via webhooks
- ✅ **Django Integration** - Middleware, authentication backend, and decorators
- ✅ **Type Hints** - Full type annotations for better IDE support
- ✅ **Production Ready** - Battle-tested and secure

## Quick Start

### 1. Install the package
```bash
pip install onehux-sso-client
```

### 2. Configure settings.py
```python
INSTALLED_APPS = [
    'onehux_sso_client',
    'accounts',  # Your app with User model
    ...
]

AUTH_USER_MODEL = 'accounts.User'
```

### 3. Create your User model
You have four ways you can create your user models to work with this package

**Option 1: Mixin (Recommended)**
```python
# myproject/models.py
from django.contrib.auth.models import AbstractUser
from onehux_sso_client.models import OnehuxSSOUserMixin

class User(OnehuxSSOUserMixin, AbstractUser):
    """Custom user with SSO support + your own fields"""
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'users'
```

**Option 2: Minimal Integration**
For users who just want SSO without profile sync:
```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    onehux_user_id = models.UUIDField(unique=True, null=True)
    # You handle profile sync yourself
```

**Option 3: Use management command (easiest)**
```bash
python manage.py onehux_init --app=accounts
```

**Option 4: Copy template manually**

Download the [user_model_template.py](https://github.com/onehuxco/onehux-sso-client/blob/main/onehux_sso_client/templates/user_model_template.py) 
and save it as `accounts/models.py`.

**Option 5: Copy from installed package**
```bash
cp $(python -c "import onehux_sso_client; print(onehux_sso_client.__path__[0])")/templates/user_model_template.py accounts/models.py
```

**Below is the complete user model, incase if you need it**
```python

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import datetime
import logging
from uuid6 import uuid7

logger = logging.getLogger(__name__)


class OnehuxSSOUserMixin(models.Model):
    """
    Mixin to add Onehux SSO fields to any User model.
    
    Usage in your project:
        from django.contrib.auth.models import AbstractUser
        from sso_client.models import OnehuxSSOUserMixin
        
        class User(OnehuxSSOUserMixin, AbstractUser):
            # Add your custom fields here
            department = models.CharField(max_length=100)
            pass
    """
    
    # Identity Provider Sync
    onehux_user_id = models.UUIDField(
        unique=True,
        default=uuid7,  # Use uuid7 as default
        blank=True,
        editable=False,
        null=True,
        db_index=True,
        help_text="User ID from Onehux Accounts Identity Provider"
    )
    
    # Profile fields synced from IdP
    full_name = models.CharField(max_length=50,blank=True)
    profile_picture_url = models.URLField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Organization & Role (single organization)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    organization_name = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=50, blank=True, db_index=True)
    
    # Sync metadata
    profile_version = models.IntegerField(default=1)
    last_synced_at = models.DateTimeField(auto_now=True)
    idp_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Verification status
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True  # ← CRITICAL: Makes this a mixin, not a concrete model
    


    # ========================================================================
    # ROLE CHECK METHODS
    # ========================================================================
    
    def has_role(self, role_slug):
        """
        Check if user has a specific role in THIS organization.
        
        Args:
            role_slug: Role slug (e.g., 'admin', 'developer')
        
        Returns:
            bool: True if user has this role
        """
        return self.role == role_slug
    
    def has_any_role(self, *role_slugs):
        """
        Check if user has any of the specified roles.
        
        Args:
            role_slugs: Variable number of role slugs
        
        Returns:
            bool: True if user has at least one of the roles
        """
        return self.role in role_slugs
    
    def is_admin(self):
        """Check if user is admin or owner"""
        return self.role in ['admin', 'owner']
    
    def is_owner(self):
        """Check if user is owner"""
        return self.role == 'owner'
    
    def is_member(self):
        """Check if user is at least a member"""
        return bool(self.role)
    
    # ========================================================================
    # ORGANIZATION METHODS
    # ========================================================================
    
    def belongs_to_organization(self, org_id):
        """
        Check if user belongs to the specified organization.
        
        Args:
            org_id: Organization UUID (string or UUID object)
        
        Returns:
            bool: True if this is the user's organization
        """
        if not self.organization_id:
            return False
        return str(self.organization_id) == str(org_id)
    
    # ========================================================================
    # PROFILE METHODS
    # ========================================================================
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def get_profile_picture_url(self):
        """Get profile picture URL with fallback"""
        if self.profile_picture_url:
            return self.profile_picture_url
        return f"{settings.STATIC_URL}images/default-avatar.png"
    
    def needs_sync(self):
        """
        Check if user data might be stale and needs syncing.
        
        Returns:
            bool: True if last sync was more than 1 hour ago
        """
        from datetime import timedelta
        if not self.last_synced_at:
            return True
        
        threshold = timezone.now() - timedelta(hours=1)
        return self.last_synced_at < threshold
    
    # ========================================================================
    # SYNC HELPER METHOD - UPDATED FOR SINGLE ORGANIZATION
    # ========================================================================
    def update_from_idp(self, user_data):
        """
        Update local user data from IdP user_data.
        
        FIXED: Now properly maps OIDC standard claim names.
        """
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Username
        self.username = (
            user_data.get('username') or 
            user_data.get('preferred_username') or 
            self.username
        )
        
        # Name fields - Accept OIDC standard OR legacy format
        self.first_name = (
            user_data.get('given_name') or      # ← OIDC standard
            user_data.get('first_name') or      # ← Legacy
            ''
        )
        
        self.last_name = (
            user_data.get('family_name') or     # ← OIDC standard
            user_data.get('last_name') or       # ← Legacy
            ''
        )
        
        self.full_name = (
            user_data.get('name') or            # ← OIDC standard
            user_data.get('full_name') or       # ← Legacy
            ''
        )
        
        # Email
        self.email = user_data.get('email', self.email)
        self.is_email_verified = (
            user_data.get('email_verified') or  # ← OIDC standard
            user_data.get('is_verified') or     # ← Legacy
            False
        )
        
        # Profile picture - Accept OIDC standard OR legacy format
        self.profile_picture_url = (
            user_data.get('picture') or         # ← OIDC standard
            user_data.get('profile_picture') or # ← Legacy
            ''
        )
        
        # Extended profile
        self.bio = user_data.get('bio', '')
        self.country = user_data.get('country', '')
        self.region = user_data.get('region', '')
        self.phone_number = user_data.get('phone_number', '')
        
        # Date of birth - OIDC standard: birthdate
        if user_data.get('birthdate'):
            try:
                self.date_of_birth = datetime.fromisoformat(
                    user_data['birthdate']
                ).date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse birthdate: {e}")
        
        # Phone verification
        self.is_phone_verified = user_data.get('phone_number_verified', False)
        
        # Organization and role
        self.role = user_data.get('role', '')
        self.organization_id = user_data.get('organization_id')
        self.organization_name = user_data.get('organization_name', '')
        
        # Sync metadata
        self.profile_version = user_data.get('profile_version', self.profile_version)
        
        # Handle updated_at
        if user_data.get('updated_at'):
            try:
                updated_at = user_data['updated_at']
                
                if isinstance(updated_at, (int, float)):
                    from django.utils import timezone as django_tz
                    self.idp_updated_at = datetime.fromtimestamp(
                        updated_at, 
                        tz=django_tz.get_current_timezone()
                    )
                elif isinstance(updated_at, str):
                    self.idp_updated_at = datetime.fromisoformat(
                        updated_at.replace('Z', '+00:00')
                    )
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Could not parse updated_at: {e}")
        
        self.save()
        
        logger.info(
            f"✓ Synced user {self.email}: {self.first_name} {self.last_name}"
        )


        # ========================================================================
        # DISPLAY METHODS
        # ========================================================================
        
        def get_role_display(self):
            """Get human-readable role name"""
            role_names = {
                'owner': 'Owner',
                'admin': 'Administrator',
                'member': 'Member',
                'viewer': 'Viewer',
                'developer': 'Developer',
                'manager': 'Manager',
                'support': 'Support',
            }
            return role_names.get(self.role, self.role.title() if self.role else 'No Role')
        
        def get_organization_display(self):
            """Get organization display string"""
            if self.organization_name:
                return self.organization_name
            elif self.organization_id:
                return f"Organization {str(self.organization_id)[:8]}"
            return "No Organization"
        

```







### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Add onehux configuration to your settings.py
```python
# Onehux SSO Configuration
ONEHUX_SSO = {
    'CLIENT_ID': env('CLIENT_ID'),
    'CLIENT_SECRET': env('CLIENT_SECRET'),
    'REDIRECT_URI': env('REDIRECT_URI'),  # http://client.onehux.com/sso/callback/
    
    # IdP Endpoints
    'AUTHORIZATION_URL': env('AUTHORIZATION_URL'),  # http://accounts.onehux.com/sso/authorize/
    'TOKEN_URL': env('TOKEN_URL'),  # http://accounts.onehux.com/sso/token/
    'USERINFO_URL': env('USERINFO_URL'),  # http://accounts.onehux.com/sso/userinfo/
    'LOGOUT_URL': env('LOGOUT_URL'),  # http://accounts.onehux.com/sso/logout/
    'JWKS_URL': env('JWKS_URL'),  # http://accounts.onehux.com/sso/.well-known/jwks.json
    
    # Security
    'USE_PKCE': True,  # Highly recommended
    'VERIFY_SSL': False,  # Set to True in production
    
    # Scopes
    'SCOPES': 'openid profile email',
    
    # Token Management
    'TOKEN_REFRESH_THRESHOLD': 300,  # Refresh 5 minutes before expiry
    
    # Webhook
    'WEBHOOK_SECRET': env('WEBHOOK_SECRET'),
    'WEBHOOK_ENDPOINT': '/sso/api/webhooks/onehux/',
}

# ============================================================================
# PUBLIC PATHS CONFIGURATION (CRITICAL FOR SAAS)
# ============================================================================
# Define which paths are accessible WITHOUT authentication
# The SilentSSOMiddleware will NOT run on these paths

SSO_PUBLIC_PATHS = [
    # Core Public Pages
    '/',                    # Homepage
    '/about/',
    '/pricing/',
    '/features/',
    '/contact/',
    '/faq/',
    
    # Content Pages
    '/blog/',
    '/docs/',
    '/help/',
    '/support/',
    
    # Legal Pages
    '/legal/',
    '/privacy/',
    '/terms/',
    '/cookies/',
    
    # Authentication Pages (if you have native login)
    '/signup/',
    '/login/',
    '/forgot-password/',
    '/reset-password/',
    
    # Public API Endpoints
    '/api/public/',
    '/api/docs/',
    
    # Health Checks
    '/health/',
    '/status/',
]

# ============================================================================
# SILENT SSO CONFIGURATION
# ============================================================================

# Enable/disable silent SSO (auto-login if IdP session exists)
SSO_SILENT_AUTH_ENABLED = True

# Optional: Additional paths to ignore for silent SSO (beyond public paths)
# Use this for monitoring endpoints, admin pages, etc.
SSO_SILENT_AUTH_IGNORED_PATHS = [
    '/health/',
    '/metrics/',
    '/monitoring/',
]

# ============================================================================
# TOKEN REFRESH CONFIGURATION
# ============================================================================

# Paths to exclude from token refresh checks
SSO_TOKEN_REFRESH_EXCLUDED_PATHS = [
    '/health/',
    '/metrics/',
    '/monitoring/',
]

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # =========================================================================
    # ONEHUX SSO MIDDLEWARES (Order matters!)
    # =========================================================================
    # 1. Silent SSO - tries to auto-login anonymous users on protected pages
    'onehux_sso_client.middleware.SilentSSOMiddleware',
    
    # 2. Token Refresh - auto-refreshes expired tokens for authenticated users
    'onehux_sso_client.middleware.SSOTokenRefreshMiddleware',
    
    # 3. Rate Limiting (Optional)
    # 'onehux_sso_client.middleware.SSORateLimitMiddleware',
]

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

# Custom authentication backend for SSO
AUTHENTICATION_BACKENDS = [
    'onehux_sso_client.backends.OnehuxSSOBackend',  # SSO authentication
    'django.contrib.auth.backends.ModelBackend',     # Fallback (superuser)
]

# Custom user model (if using OnehuxSSOUserMixin)
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs

# Where `login_required` / `@login_required` should redirect
# when an anonymous user hits a protected page
LOGIN_URL = 'sso:sso_login'  # Redirect to SSO login

# Where to send the user after they click "log out"
LOGOUT_REDIRECT_URL = '/'

# Where to send the user after a *successful* login
LOGIN_REDIRECT_URL = 'accounts:dashboard'          # or '/dashboard/'

# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_SECURE = False  # Set to True in production (HTTPS only)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================

# Custom admin URL (for security)
ADMIN_URL = env('ADMIN_URL', default='admin')
ADMIN_LOGIN_PATH = f'/{ADMIN_URL}/'
```

### 6. Add url pattern to your project main urls.py
```python
from django.urls import path, include

urlpatterns = [
    # ...
    
    # =========================================================================
    # SSO ENDPOINTS / URLS
    # =========================================================================
    path('sso/', include('onehux_sso_client.urls', namespace='sso')),
    
    # ...
]
```

### 7. Protecting Views in Service Providers

#### Function-Based Views (FBV)

Use decorators to protect function-based views:
```python
from onehux_sso_client.decorators import (
    sso_login_required,      # Basic SSO auth
    require_sso_role,        # Specific role
    require_any_role,        # Multiple roles
    require_all_roles,       # All roles required
    require_sso_permission,  # Permission-based
)

# Basic SSO protection
@sso_login_required
def dashboard(request):
    return render(request, 'dashboard.html')

# Only owners can access
@require_sso_role('owner')
def owner_panel(request):
    return render(request, 'owner_panel.html')

# Owners OR admins can access
@require_any_role('owner', 'admin')
def management(request):
    return render(request, 'management.html')

# Must have BOTH roles
@require_all_roles('admin', 'developer')
def admin_dev_tools(request):
    return render(request, 'admin_dev.html')

# Permission-based protection
@require_sso_permission('can_delete_posts')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    return redirect('posts:list')
```

#### Class-Based Views (CBV)

For class-based views, use the provided mixins instead of decorators:
```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from onehux_sso_client.mixins import (
    SSOLoginRequiredMixin,         # Basic SSO authentication
    SSORequireRoleMixin,           # Single role requirement
    SSORequireAnyRoleMixin,        # Multiple role options
    SSORequireAllRolesMixin,       # All roles required
    SSORequirePermissionMixin,     # Permission-based
    APISSOLoginRequiredMixin,      # For API views
)
```

**Basic Authentication Protection:**
```python
from django.views.generic import TemplateView, CreateView
from onehux_sso_client.mixins import SSOLoginRequiredMixin

# Simple protected view
class DashboardView(SSOLoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

# Protected create view
class ArticleCreateView(SSOLoginRequiredMixin, CreateView):
    model = Article
    fields = ['title', 'content']
    template_name = 'article_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
```

**Single Role Protection:**
```python
from onehux_sso_client.mixins import SSORequireRoleMixin, SSOLoginRequiredMixin

class AdminDashboardView(SSORequireRoleMixin, SSOLoginRequiredMixin, TemplateView):
    """Only users with 'admin' role can access"""
    template_name = 'admin/dashboard.html'
    required_role = 'admin'  # ← Set required role

class ManagerPanelView(SSORequireRoleMixin, SSOLoginRequiredMixin, ListView):
    """Only managers can view this list"""
    model = Report
    template_name = 'manager/reports.html'
    required_role = 'manager'
    paginate_by = 25
```

**Multiple Role Options (Any Role):**
```python
from onehux_sso_client.mixins import SSORequireAnyRoleMixin, SSOLoginRequiredMixin

class ContentModerationView(SSORequireAnyRoleMixin, SSOLoginRequiredMixin, ListView):
    """Accessible by admin, moderator, or editor"""
    model = Content
    template_name = 'moderation/content_list.html'
    required_roles = ['admin', 'moderator', 'editor']  # ← User needs ANY of these
    
    def get_queryset(self):
        return Content.objects.filter(status='pending')
```

**Multiple Roles Required (All Roles):**
```python
from onehux_sso_client.mixins import SSORequireAllRolesMixin, SSOLoginRequiredMixin

class AdminDeveloperView(SSORequireAllRolesMixin, SSOLoginRequiredMixin, TemplateView):
    """User must have BOTH admin AND developer roles"""
    template_name = 'admin_dev/tools.html'
    required_roles = ['admin', 'developer']  # ← User needs ALL of these
```

**Permission-Based Protection:**
```python
from onehux_sso_client.mixins import SSORequirePermissionMixin, SSOLoginRequiredMixin

class DeleteUserView(SSORequirePermissionMixin, SSOLoginRequiredMixin, DeleteView):
    """Only users with 'can_delete_users' permission can delete"""
    model = User
    template_name = 'users/confirm_delete.html'
    required_permission = 'can_delete_users'  # ← Set required permission
    success_url = '/users/'
```

**Combining Multiple Protections:**
```python
from onehux_sso_client.mixins import (
    SSORequireRoleMixin,
    SSORequirePermissionMixin,
    SSOLoginRequiredMixin
)

class FeaturedContentUpdateView(
    SSORequireRoleMixin,           # Must have 'admin' role
    SSORequirePermissionMixin,      # AND 'can_feature_content' permission
    SSOLoginRequiredMixin,          # AND be authenticated
    UpdateView
):
    """Requires both specific role AND permission"""
    model = Content
    template_name = 'content/feature_form.html'
    required_role = 'admin'
    required_permission = 'can_feature_content'
    fields = ['featured', 'featured_until']
```

**API Views (JSON Response):**
```python
from django.views import View
from django.http import JsonResponse
from onehux_sso_client.mixins import APISSOLoginRequiredMixin

class APIDataView(APISSOLoginRequiredMixin, View):
    """
    API endpoint that returns JSON errors instead of redirects
    Returns 401 with JSON error if not authenticated
    """
    
    def get(self, request):
        data = {
            'user': request.user.username,
            'email': request.user.email,
            'data': 'sensitive information'
        }
        return JsonResponse(data)

class APIStatsView(APISSOLoginRequiredMixin, View):
    """Protected API endpoint"""
    
    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'active_sessions': SSOSession.objects.filter(is_active=True).count()
        }
        return JsonResponse(stats)
```

**Real-World Example - E-commerce:**
```python
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from onehux_sso_client.mixins import (
    SSOLoginRequiredMixin,
    SSORequireRoleMixin,
    SSORequireAnyRoleMixin,
)

# Customer can view their orders
class MyOrdersView(SSOLoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/my_orders.html'
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

# Admin can view all orders
class AllOrdersView(SSORequireRoleMixin, SSOLoginRequiredMixin, ListView):
    model = Order
    template_name = 'admin/all_orders.html'
    required_role = 'admin'
    paginate_by = 50

# Admin or warehouse staff can update order status
class UpdateOrderStatusView(SSORequireAnyRoleMixin, SSOLoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'orders/update_status.html'
    required_roles = ['admin', 'warehouse_staff']
    fields = ['status', 'tracking_number']

# Only admin can delete orders
class DeleteOrderView(SSORequireRoleMixin, SSOLoginRequiredMixin, DeleteView):
    model = Order
    template_name = 'orders/confirm_delete.html'
    required_role = 'admin'
    success_url = '/orders/'
```

#### Important Notes

1. **Mixin Order Matters** - Always place `SSOLoginRequiredMixin` last (rightmost) in the inheritance chain:
```python
   # ✅ CORRECT - SSOLoginRequiredMixin runs first
   class MyView(SSORequireRoleMixin, SSOLoginRequiredMixin, TemplateView):
       pass
   
   # ❌ WRONG - Auth check won't run first
   class MyView(SSOLoginRequiredMixin, SSORequireRoleMixin, TemplateView):
       pass
```

2. **Set Required Attributes** - Don't forget to set `required_role`, `required_roles`, or `required_permission`:
```python
   # ✅ CORRECT
   class AdminView(SSORequireRoleMixin, SSOLoginRequiredMixin, TemplateView):
       required_role = 'admin'
   
   # ❌ WRONG - Will raise ValueError
   class AdminView(SSORequireRoleMixin, SSOLoginRequiredMixin, TemplateView):
       pass  # Missing required_role!
```

3. **Custom 403 Template** - Create `templates/onehux_sso_client/403.html` for unauthorized access pages:
```html
   <!-- templates/onehux_sso_client/403.html -->
   {% extends 'base.html' %}
   
   {% block content %}
   <div class="error-page">
       <h1>403 - Access Denied</h1>
       <p>You don't have permission to access this page.</p>
       {% if required_role %}
           <p>Required role: <strong>{{ required_role }}</strong></p>
       {% endif %}
       {% if required_roles %}
           <p>Required roles: <strong>{{ required_roles|join:", " }}</strong></p>
       {% endif %}
       <p>Your roles: {{ user_roles|join:", "|default:"None" }}</p>
       <a href="{% url 'home' %}">Go Home</a>
   </div>
   {% endblock %}
```

4. **Alternative: Method Decorator** - If you prefer using decorators on CBVs (not recommended):
```python
   from django.utils.decorators import method_decorator
   from onehux_sso_client.decorators import sso_login_required, require_sso_role
   
   @method_decorator(sso_login_required, name='dispatch')
   class MyView(TemplateView):
       template_name = 'my_template.html'
   
   # Multiple decorators
   decorators = [sso_login_required, require_sso_role('admin')]
   
   @method_decorator(decorators, name='dispatch')
   class AdminView(TemplateView):
       template_name = 'admin.html'
```
   
   **However, using mixins (shown above) is the recommended Django approach.**

## Advanced Usage

### Manual OAuth2 Flow
```python
from onehux_sso_client import OnehuxClient

# Initialize client
client = OnehuxClient(
    client_id='your-client-id',
    client_secret='your-client-secret',
    redirect_uri='http://yourapp.com/oauth/callback',
    onehux_base_url='https://accounts.onehux.com'
)

# 1. Generate authorization URL
auth_url, state, code_verifier = client.get_authorization_url(
    scopes=['openid', 'profile', 'email']
)

# Store state and code_verifier in session, then redirect user to auth_url

# 2. Exchange authorization code for tokens (in callback view)
tokens = client.exchange_code_for_tokens(
    code='authorization-code',
    code_verifier=code_verifier
)

# 3. Get user information
user_info = client.get_user_info(tokens['access_token'])

# 4. Verify ID token (optional)
id_token_payload = client.verify_id_token(tokens['id_token'])
```

### Token Refresh
```python
# Refresh an expired access token
new_tokens = client.refresh_access_token(refresh_token)
```

### Webhook Handling

Onehux sends webhooks for user events (login, logout, profile updates). The client automatically handles these via the `onehux_webhook` view.

**Webhook Events:**
- `user.login` - User logged into your application
- `user.logout` - User logged out (global SLO)
- `user.updated` - User profile was updated

**Webhook Payload Example:**
```json
{
  "event": "user.updated",
  "timestamp": "2024-01-15T12:00:00Z",
  "user": {
    "sub": "user-uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "given_name": "John",
    "family_name": "Doe",
    "profile_version": 5
  }
}
```

## Configuration Options

| Setting | Required | Description |
|---------|----------|-------------|
| `ONEHUX_CLIENT_ID` | Yes | Your application's client ID from Onehux |
| `ONEHUX_CLIENT_SECRET` | Yes | Your application's client secret |
| `ONEHUX_REDIRECT_URI` | Yes | OAuth2 callback URL |
| `ONEHUX_BASE_URL` | No | Onehux platform URL (default: https://accounts.onehux.com) |
| `ONEHUX_WEBHOOK_SECRET` | No | Secret for webhook signature verification |
| `ONEHUX_LOGIN_URL` | No | Custom login URL (default: /oauth/login/) |

## Security Features

- **PKCE (Proof Key for Code Exchange)** - Protects against authorization code interception
- **State Parameter** - CSRF protection for OAuth2 flow
- **Webhook Signature Verification** - HMAC-SHA256 validation
- **Token Validation** - JWT signature verification with RSA keys
- **Secure Token Storage** - Session-based token management

## Development
```bash
# Clone the repository
git clone https://github.com/programmerisaac/onehux-sso-client.git
cd onehux-sso-client

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black onehux_sso_client/

# Lint code
flake8 onehux_sso_client/
```

## Example Application

See the [example-service-provider](./examples/service_provider/) directory for a complete Django application demonstrating SSO/SLO integration.

## Support

- **Documentation**: https://docs.onehux.com
- **Issues**: https://github.com/programmerisaac/onehux-sso-client/issues
- **Email**: support@onehux.com

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## Changelog

### 2.3.1 (2026-01-17)
- Bug fixes

### 2.3.0 (2026-01-11)
- Bug fixes (revoke token)

### 2.0.0 (2026-01-01)
- Bug fixes
- Replace pkg_resources with modern importlib.metadata
- Added Mixins for Class Base Views


### 1.0.0 (2025-12-18)
- Bug fixes
- Improved token validation
- Better error handling
- Single Logout bug fix
- Properly synchronize user data across service providers

### 0.1.0 (2025-12-15)
- Initial release
- OAuth2/OIDC authentication with PKCE


