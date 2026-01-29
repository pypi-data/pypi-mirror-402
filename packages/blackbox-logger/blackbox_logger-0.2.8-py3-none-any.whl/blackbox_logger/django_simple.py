# blackbox_logger/django_simple.py
"""
Ultra-simple Django integration for BlackBox Logger
Just add one line to your settings.py - that's it!
"""

try:
    from .django_middleware import BlackBoxLoggerMiddleware
except ImportError:
    # Django not available - create a dummy class
    class BlackBoxLoggerMiddleware:
        def __init__(self, get_response=None):
            raise ImportError("Django is required for BlackBoxLoggerMiddleware. Install Django or use HTTPLogger directly.")

# That's it! Just import this in your Django project
# Add 'blackbox_logger.django_simple.BlackBoxLoggerMiddleware' to MIDDLEWARE
