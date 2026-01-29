import json
import traceback
import requests
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .exceptions import AIssueConfigurationError, AIssueAPIError

logger = logging.getLogger(__name__)


class AIssueMiddleware:
    """
    Django middleware for logging errors to AIssue error monitoring service.
    
    Configuration in settings.py:
    AISSUE_API_KEY = 'your-api-key'
    AISSUE_BASE_URL = 'https://your-aissue-instance.com'  # optional
    AISSUE_TIMEOUT = 5  # optional, default 5 seconds
    AISSUE_ENABLED = True  # optional, default True
    AISSUE_LOG_IN_DEBUG = False  # optional, allows logging in DEBUG mode
    
    By default, errors are only logged when DEBUG = False.
    Set AISSUE_LOG_IN_DEBUG = True to also log errors in DEBUG mode.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._validate_config()
        
    def _validate_config(self):
        """Validate AIssue configuration"""
        self.api_key = getattr(settings, 'AISSUE_API_KEY', None)
        if not self.api_key:
            raise AIssueConfigurationError(
                "AISSUE_API_KEY setting is required for AIssueMiddleware"
            )
        
        self.base_url = getattr(settings, 'AISSUE_BASE_URL', 'https://app.aissue.com')
        self.timeout = getattr(settings, 'AISSUE_TIMEOUT', 5)
        self.enabled = getattr(settings, 'AISSUE_ENABLED', True)
        self.log_in_debug = getattr(settings, 'AISSUE_LOG_IN_DEBUG', False)
        
        # Check if we should log based on DEBUG setting
        debug_mode = getattr(settings, 'DEBUG', False)
        self.should_log = self.enabled and (not debug_mode or self.log_in_debug)
        
        logger.info(f"AIssue middleware initialized: {self.base_url} (enabled: {self.should_log})")

    def __call__(self, request):
        """Process the request and response"""
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            if self.should_log:
                try:
                    self._log_error(request, e)
                except Exception as log_error:
                    # Never let error logging break the application
                    logger.warning(f"Failed to log error to AIssue: {log_error}")
            raise  # Re-raise the original exception
    
    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        This is the proper Django hook for exception handling.
        Returns None to allow normal Django error handling to continue.
        """
        if self.should_log:
            try:
                self._log_error(request, exception)
            except Exception as e:
                # Never let error logging break the application
                logger.warning(f"Failed to log error to AIssue: {e}")
        
        # Return None to let Django handle the exception normally
        # This prevents duplicate processing and maintains Django's error flow
        return None

    def _log_error(self, request, exception):
        """Send error data to AIssue"""
        try:
            error_data = self._extract_error_data(request, exception)
            self._send_to_aissue(error_data)
            logger.debug("Error successfully logged to AIssue")
        except Exception as e:
            raise AIssueAPIError(f"Failed to log error to AIssue: {e}")

    def _extract_error_data(self, request, exception):
        """Extract relevant error information from request and exception"""
        # Get request body
        body = self._get_request_body(request)
        
        return {
            'error_code': getattr(exception, 'status_code', 500),
            'path': request.path,
            'method': request.method,
            'user_email': self._get_user_email(request),
            'user_id': self._get_user_id(request),
            'traceback': traceback.format_exc(),
            'request_data': {
                'GET': dict(request.GET),
                'POST': dict(request.POST),
                'body': body
            },
            'headers': dict(request.headers)
        }

    def _get_request_body(self, request):
        """Safely extract request body"""
        try:
            body = request.body.decode('utf-8') if request.body else None
            if body and 'application/json' in request.content_type.lower():
                return json.loads(body)
            return body
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            return None

    def _get_user_email(self, request):
        """Safely get user email"""
        if hasattr(request, 'user') and hasattr(request.user, 'email'):
            return request.user.email
        return None

    def _get_user_id(self, request):
        """Safely get user ID"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            return str(request.user.id)
        return None

    def _send_to_aissue(self, error_data):
        """Send error data to AIssue API"""
        try:
            response = requests.post(
                f"{self.base_url.rstrip('/')}/api/errors/",
                json=error_data,
                headers={'X-API-Key': self.api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"AIssue API error: {e}") 