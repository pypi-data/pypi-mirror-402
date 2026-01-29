from .logger import HTTPLogger

# Django integration (optional - only import if Django is available)
try:
    from .django_simple import BlackBoxLoggerMiddleware
    # Django users: Just add 'blackbox_logger.BlackBoxLoggerMiddleware' to MIDDLEWARE
except ImportError:
    # Django not installed - that's fine, users can still use HTTPLogger directly
    pass
