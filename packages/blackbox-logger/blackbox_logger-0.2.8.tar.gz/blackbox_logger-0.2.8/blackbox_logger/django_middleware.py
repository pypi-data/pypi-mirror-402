# blackbox_logger/django_middleware.py
"""
Ultra-simple Django middleware for BlackBox Logger
Optimized for performance with minimal overhead
"""

import json
import time
import threading
from queue import Queue

# Django imports with fallback
try:
    from django.conf import settings
    from django.utils.deprecation import MiddlewareMixin
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    # Create dummy classes for when Django is not available
    class MiddlewareMixin:
        def __init__(self, get_response=None):
            self.get_response = get_response

from .masking import mask_sensitive_data
from .loggers.file_logger import setup_file_logger
from .loggers.sqlite_logger import SQLiteLogger

# Global instances (created once)
file_logger = setup_file_logger()
sqlite_logger = SQLiteLogger()

# Background logging queue
log_queue = Queue()
log_thread = None

def background_logger():
    """Background thread to handle logging without blocking requests"""
    while True:
        try:
            log_data = log_queue.get(timeout=1)
            if log_data is None:  # Shutdown signal
                break
            
            log_type, method, path, user, ip, user_agent, payload, status_code = log_data
            
            # File logging (fast)
            msg = f"[{log_type.upper()}] {method} {path} | User: {user} | IP: {ip} | Payload: {payload}"
            if status_code:
                msg += f" | Status: {status_code}"
            file_logger.info(msg)
            
            # Database logging (async)
            sqlite_logger.log(log_type, method, path, user, ip, user_agent, payload, status_code)
            
        except Exception as e:
            pass

# Start background thread
if log_thread is None or not log_thread.is_alive():
    log_thread = threading.Thread(target=background_logger, daemon=True)
    log_thread.start()

class BlackBoxLoggerMiddleware(MiddlewareMixin):
    """
    Ultra-simple Django middleware for request/response logging
    - Minimal performance impact
    - Background logging
    - Django-optimized
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.excluded_paths = [
            '/admin/', '/static/', '/media/', '/favicon.ico',
            '/health/', '/metrics/', '/__debug__/',
            # Add common file upload endpoints
            '/upload/', '/uploads/', '/files/', '/attachments/',
            '/epic_live_run_new_job/',  # Your specific endpoint
        ]
    
    def process_request(self, request):
        """Log request with minimal overhead"""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return
        
        # Start timing
        request._blackbox_start_time = time.time()
        
        # Get basic info (fast operations only)
        user = self._get_user_simple(request)
        ip = self._get_ip_simple(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Simple body processing (no complex parsing)
        body = self._get_body_simple(request)
        
        # Queue for background processing
        log_queue.put(('request', request.method, request.path, user, ip, user_agent, body, None))
    
    def process_response(self, request, response):
        """Log response with minimal overhead"""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return response
        
        # Get basic info
        user = self._get_user_simple(request)
        ip = self._get_ip_simple(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Simple response processing
        response_body = self._get_response_body_simple(response)
        
        # Calculate duration
        duration = time.time() - getattr(request, '_blackbox_start_time', time.time())
        
        # Queue for background processing
        log_queue.put(('response', request.method, request.path, user, ip, user_agent, response_body, response.status_code))
        
        return response
    
    def _get_user_simple(self, request):
        """Simple user detection for Django"""
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                return str(request.user)
        except:
            pass
        return 'Anonymous'
    
    def _get_ip_simple(self, request):
        """Simple IP detection for Django"""
        try:
            # Check for forwarded IP first
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0].strip()
            return request.META.get('REMOTE_ADDR', 'Unknown')
        except:
            return 'Unknown'
    
    def _get_body_simple(self, request):
        """Simple body processing - no complex parsing"""
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                content_type = getattr(request, 'content_type', '')
                
                # Skip multipart/form-data (file uploads) - too large and not useful
                if 'multipart/form-data' in content_type:
                    return '[File upload - content skipped]'
                
                # Skip binary content types
                if any(binary_type in content_type for binary_type in ['application/pdf', 'image/', 'video/', 'audio/']):
                    return f'[Binary {content_type} - content skipped]'
                
                body = request.body.decode('utf-8', errors='ignore')
                
                # Skip very large bodies
                if len(body) > 5000:
                    return f'[Request too large: {len(body)} chars]'
                
                # Simple JSON masking (only if it's JSON)
                if 'application/json' in content_type:
                    try:
                        data = json.loads(body)
                        masked_data = mask_sensitive_data(data)
                        return json.dumps(masked_data)
                    except:
                        return body[:1000]  # Limit size
                
                return body[:1000]  # Limit size
            return ''
        except:
            return '[Error reading body]'
    
    def _get_response_body_simple(self, response):
        """Simple response processing"""
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')
                
                # Skip very large responses
                if len(content) > 2000:
                    return f'[Response too large: {len(content)} chars]'
                
                # Skip HTML responses (usually not useful for logging)
                if any(html_indicator in content.lower() for html_indicator in ['<html', '<!doctype', '<body']):
                    return '[HTML response - content skipped]'
                
                return content
            return '[No content]'
        except:
            return '[Error reading response]'
