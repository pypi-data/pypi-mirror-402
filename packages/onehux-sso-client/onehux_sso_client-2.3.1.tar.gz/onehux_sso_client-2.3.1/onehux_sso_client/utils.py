# onehux_sso_client/utils.py

"""
Utility functions and classes for Onehux SSO Client integration.

Includes:
- OnehuxSSOClient: Main SSO client for OAuth2/OIDC flows
- SSOSessionManager: Session management for tokens and user info
"""

import secrets
import hashlib
import base64
import requests
import jwt
import logging
from datetime import timedelta
from urllib.parse import urlencode
from importlib import resources, metadata  # Modern replacement for pkg_resources

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ============================================================================
# SSO SESSION MANAGER
# ============================================================================

class SSOSessionManager:
    """
    Manages SSO tokens and user info in Django session.
    """
    
    @staticmethod
    def store_tokens(request, token_response):
        """Store OAuth tokens in session."""
        request.session['sso_access_token'] = token_response.get('access_token')
        request.session['sso_refresh_token'] = token_response.get('refresh_token')
        request.session['sso_id_token'] = token_response.get('id_token')
        request.session['sso_token_type'] = token_response.get('token_type', 'Bearer')
        
        # Calculate expiration time (with 5 minute buffer)
        expires_in = token_response.get('expires_in', 3600)
        expiration_time = timezone.now() + timedelta(seconds=expires_in - 300)
        request.session['sso_token_expires_at'] = expiration_time.isoformat()
        
        request.session.modified = True
        logger.info("SSO tokens stored in session")

    @staticmethod
    def get_access_token(request):
        return request.session.get('sso_access_token')

    @staticmethod
    def get_refresh_token(request):
        return request.session.get('sso_refresh_token')

    @staticmethod
    def is_token_expired(request):
        expiration_str = request.session.get('sso_token_expires_at')
        if not expiration_str:
            return True
        try:
            expiration_time = timezone.datetime.fromisoformat(expiration_str)
            return timezone.now() >= expiration_time
        except (ValueError, TypeError):
            return True

    @staticmethod
    def refresh_token_if_needed(request):
        if not SSOSessionManager.is_token_expired(request):
            return True
        
        refresh_token = SSOSessionManager.get_refresh_token(request)
        if not refresh_token:
            logger.warning("No refresh token available for token refresh")
            return False
        
        client = OnehuxSSOClient()
        token_response = client.refresh_access_token(refresh_token)
        
        if not token_response:
            logger.error("Token refresh failed")
            return False
        
        SSOSessionManager.store_tokens(request, token_response)
        return True

    @staticmethod
    def clear_session(request):
        sso_keys = [
            'sso_access_token', 'sso_refresh_token', 'sso_id_token',
            'sso_token_type', 'sso_token_expires_at', 'sso_user_info',
            'oauth_state', 'oauth_nonce', 'oauth_code_verifier',
            'login_next_url', 'sso_auto_check_done',
        ]
        for key in sso_keys:
            request.session.pop(key, None)
        request.session.modified = True
        logger.info("SSO session data cleared")


# ============================================================================
# ONEHUX SSO CLIENT
# ============================================================================

class OnehuxSSOClient:
    def __init__(self):
        self.config = settings.ONEHUX_SSO
        self.client_id = self.config['CLIENT_ID']
        self.client_secret = self.config['CLIENT_SECRET']
        self.redirect_uri = self.config['REDIRECT_URI']

    @staticmethod
    def generate_code_verifier():
        return secrets.token_urlsafe(64)

    @staticmethod
    def generate_code_challenge(code_verifier):
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        return challenge

    @staticmethod
    def generate_state():
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_nonce():
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, request, prompt=None):
        state = self.generate_state()
        nonce = self.generate_nonce()
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        
        request.session['oauth_state'] = state
        request.session['oauth_nonce'] = nonce
        request.session['oauth_code_verifier'] = code_verifier
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.config['SCOPES'],
            'state': state,
            'nonce': nonce,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        if prompt:
            params['prompt'] = prompt
        
        auth_url = f"{self.config['AUTHORIZATION_URL']}?{urlencode(params)}"
        return auth_url, state, code_verifier

    def exchange_code_for_tokens(self, code, code_verifier):
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code_verifier': code_verifier,
        }
        try:
            response = requests.post(
                self.config['TOKEN_URL'],
                data=data,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error exchanging code: {str(e)}")
            return None

    def refresh_access_token(self, refresh_token):
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        try:
            response = requests.post(
                self.config['TOKEN_URL'],
                data=data,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None

    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(
                self.config['USERINFO_URL'],
                headers=headers,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}")
            return None



    # ========================================================================
    # TOKEN REVOCATION
    # ========================================================================
    
    def revoke_token(self, token, token_type_hint='access_token'):
        """
        Revoke an access or refresh token at the IdP.
        
        Args:
            token (str): Token to revoke
            token_type_hint (str): 'access_token' or 'refresh_token'
        
        Returns:
            bool: True if revocation request was successful
        """
        data = {
            'token': token,
            'token_type_hint': token_type_hint,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        # Build revocation URL (typically /token/revoke or /revoke)
        revoke_url = self.config.get(
            'REVOKE_URL',
            self.config['TOKEN_URL'].replace('/token/', '/revoke/')
        )
        
        try:
            response = requests.post(
                revoke_url,
                data=data,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            
            # RFC 7009: Token revocation endpoint always returns 200
            logger.info(f"Token revocation request sent: {token_type_hint}")
            return True
                
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}", exc_info=True)
            return False
        








# ============================================================================
# TEMPLATE HELPERS (MODERN IMPLEMENTATION)
# ============================================================================

def get_package_version():
    """Returns the version of the package using modern metadata API."""
    try:
        return metadata.version('onehux-sso-client')
    except metadata.PackageNotFoundError:
        return "unknown"

def get_user_model_template():
    """
    Get the user model template content as a string.
    Uses importlib.resources (Modern Python 3.9+ way).
    """
    try:
        # Replaces pkg_resources.resource_string
        return resources.files('onehux_sso_client').joinpath('templates/user_model_template.py').read_text(encoding='utf-8')
    except Exception as e:
        raise FileNotFoundError(f"Could not load user model template: {e}")

def get_template_path():
    """
    Get the file path to the user model template.
    Returns a Path object which is more robust than a string.
    """
    # Replaces pkg_resources.resource_filename
    return resources.files('onehux_sso_client').joinpath('templates/user_model_template.py')


