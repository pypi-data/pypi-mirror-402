"""
Lazy Import Utilities

Provides utilities for lazy loading models and views to avoid circular dependencies.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured


def get_model_lazy(app_label, model_name):
    """Lazy load a model to avoid circular imports.

    Args:
        app_label: The app label (e.g., 'marketplace')
        model_name: The model name (e.g., 'Product')

    Returns:
        The model class or None if not available
    """
    try:
        return apps.get_model(app_label, model_name)
    except (LookupError, ImproperlyConfigured):
        return None


def get_product_model():
    """Get the main Product model."""
    return get_model_lazy('wetail_core.marketplace', 'Product')


def get_order_model():
    """Get the main Order model."""
    return get_model_lazy('wetail_core.checkout', 'Order')


def get_user_model_lazy():
    """Get the User model.
    
    Uses Django's get_user_model() for custom user model support.
    """
    from django.contrib.auth import get_user_model as django_get_user_model
    return django_get_user_model()


def safe_import_view(module_path, view_name, fallback_view=None):
    """Safely import a view function with fallback.

    Args:
        module_path: The module path (e.g., 'myapp.views')
        view_name: The view function name
        fallback_view: Optional fallback view function

    Returns:
        The view function or fallback_view or None
    """
    try:
        from importlib import import_module
        module = import_module(module_path)
        return getattr(module, view_name, fallback_view)
    except (ImportError, AttributeError):
        return fallback_view


def safe_import_model(app_label, model_name, fallback_model=None):
    """Safely import a model with fallback.

    Args:
        app_label: The app label
        model_name: The model name
        fallback_model: Optional fallback model class

    Returns:
        The model class or fallback_model or None
    """
    model = get_model_lazy(app_label, model_name)
    return model if model is not None else fallback_model


def safe_import_class(module_path, class_name, fallback_class=None):
    """Safely import a class with fallback.

    Args:
        module_path: The module path (e.g., 'myapp.services')
        class_name: The class name
        fallback_class: Optional fallback class

    Returns:
        The class or fallback_class or None
    """
    try:
        from importlib import import_module
        module = import_module(module_path)
        return getattr(module, class_name, fallback_class)
    except (ImportError, AttributeError):
        return fallback_class


def is_app_installed(app_label):
    """Check if an app is installed and configured.

    Args:
        app_label: The app label to check

    Returns:
        True if app is installed, False otherwise
    """
    try:
        apps.get_app_config(app_label)
        return True
    except LookupError:
        return False
