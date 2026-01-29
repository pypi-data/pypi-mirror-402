"""
Error Handling Utilities

Provides comprehensive error handling for missing models and apps.
Enables graceful degradation when apps are disabled or models are unavailable.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

import logging
from functools import wraps

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.shortcuts import render

logger = logging.getLogger(__name__)


class MissingAppError(Exception):
    """Raised when a required app is not available."""
    pass


class MissingModelError(Exception):
    """Raised when a required model is not available."""
    pass


def handle_missing_app(app_name, request=None, redirect_url='/', error_message=None):
    """Handle missing app gracefully.

    Args:
        app_name: Name of the missing app
        request: Django request object (optional)
        redirect_url: URL to redirect to (default: '/')
        error_message: Custom error message

    Returns:
        HttpResponse or raises Http404
    """
    default_message = f"The {app_name} feature is currently unavailable."
    message = error_message or default_message

    logger.warning(f"Missing app accessed: {app_name}")

    if request:
        messages.error(request, message)
        return render(request, 'errors/feature_unavailable.html', {
            'app_name': app_name,
            'message': message,
            'redirect_url': redirect_url
        })
    else:
        raise Http404(message)


def handle_missing_model(model_name, request=None, return_empty=False):
    """Handle missing model gracefully.

    Args:
        model_name: Name of the missing model
        request: Django request object (optional)
        return_empty: Whether to return empty data instead of error

    Returns:
        Empty queryset/data or raises Http404
    """
    logger.warning(f"Missing model accessed: {model_name}")

    if return_empty:
        return []

    if request:
        messages.error(request, f"The {model_name} feature is currently unavailable.")
        return render(request, 'errors/feature_unavailable.html', {
            'model_name': model_name,
            'message': f"The {model_name} feature is currently unavailable.",
            'redirect_url': '/'
        })
    else:
        raise Http404(f"Model {model_name} is not available")


def get_fallback_context(missing_items=None):
    """Create a context dictionary for templates when features are unavailable.

    Args:
        missing_items: List of missing items (apps, models, etc.)

    Returns:
        Dictionary with fallback context
    """
    return {
        'feature_unavailable': True,
        'missing_items': missing_items or [],
        'fallback_message': "Some features are currently unavailable.",
        'show_fallback_ui': True
    }


def log_missing_dependency(dependency_type, dependency_name, context=""):
    """Log missing dependency for monitoring and debugging.

    Args:
        dependency_type: Type of dependency ('app', 'model', 'view', etc.)
        dependency_name: Name of the missing dependency
        context: Additional context information
    """
    logger.warning(
        f"Missing {dependency_type}: {dependency_name}",
        extra={
            'dependency_type': dependency_type,
            'dependency_name': dependency_name,
            'context': context
        }
    )


def require_models(**model_specs):
    """Decorator to require multiple models to be available.

    Usage:
        @require_models(
            Product=('marketplace_new', 'ProductListing'),
            Order=('checkout', 'Order')
        )
        def my_view(request):
            # This view requires both models
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from wetail_core.core.utils.lazy_imports import get_model_lazy

            missing_models = []
            for model_name, (app_label, model_class_name) in model_specs.items():
                model = get_model_lazy(app_label, model_class_name)
                if model is None:
                    missing_models.append(f"{app_label}.{model_class_name}")

            if missing_models:
                log_missing_dependency('models', ', '.join(missing_models), view_func.__name__)
                return handle_missing_model(', '.join(missing_models), request)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def graceful_view_error_handler(view_func):
    """Decorator to handle view errors gracefully.

    Usage:
        @graceful_view_error_handler
        def my_view(request):
            # This view will handle errors gracefully
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except (ImportError, LookupError, ImproperlyConfigured) as e:
            logger.error(f"View error in {view_func.__name__}: {e}")
            messages.error(request, "This feature is temporarily unavailable.")
            return render(request, 'errors/feature_unavailable.html', {
                'message': 'This feature is temporarily unavailable due to a system issue.',
                'redirect_url': '/'
            })
        except Exception as e:
            logger.error(f"Unexpected error in {view_func.__name__}: {e}")
            messages.error(request, "An unexpected error occurred.")
            return render(request, 'errors/feature_unavailable.html', {
                'message': 'An unexpected error occurred. Please try again later.',
                'redirect_url': '/'
            })
    return wrapper
