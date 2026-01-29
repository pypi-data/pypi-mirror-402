"""
Enterprise Feature Stubs

Provides placeholder implementations for enterprise features.
These stubs allow wetail-core to function independently while
gracefully indicating when enterprise features are accessed.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

import logging
from functools import wraps
from typing import Any, Callable, TypeVar, Optional

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class EnterpriseFeatureRequired(Exception):
    """Raised when an enterprise feature is accessed without the enterprise package."""
    
    def __init__(self, feature_name: str, message: Optional[str] = None):
        self.feature_name = feature_name
        self.message = message or (
            f"This feature requires wetail-enterprise package. "
            f"Visit https://wetail.co/enterprise for more information."
        )
        super().__init__(self.message)


class EnterpriseFeature:
    """
    Decorator and context manager for enterprise-only features.
    
    Usage:
        @EnterpriseFeature("advanced_feature")
        def my_advanced_function():
            pass
            
        # Or check availability:
        if EnterpriseFeature.is_available():
            use_enterprise_features()
    """
    
    _enterprise_available: Optional[bool] = None
    _enterprise_features: dict = {}
    
    def __init__(self, feature_name: str = "enterprise", fallback: Any = None):
        self.feature_name = feature_name
        self.fallback = fallback
    
    def __call__(self, func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.is_available(self.feature_name):
                if self.fallback is not None:
                    logger.info("Enterprise feature not available. Using fallback.")
                    if callable(self.fallback):
                        return self.fallback(*args, **kwargs)
                    return self.fallback
                raise EnterpriseFeatureRequired(self.feature_name)
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    
    @classmethod
    def is_available(cls, feature_name: Optional[str] = None) -> bool:
        """Check if enterprise package is available."""
        if cls._enterprise_available is None:
            try:
                import wetail_enterprise  # noqa: F401
                cls._enterprise_available = True
                if hasattr(wetail_enterprise, 'FEATURES'):
                    cls._enterprise_features = wetail_enterprise.FEATURES
            except ImportError:
                cls._enterprise_available = False
                cls._enterprise_features = {}
        
        if feature_name is None:
            return cls._enterprise_available
        
        return (
            cls._enterprise_available and 
            feature_name in cls._enterprise_features
        )
    
    @classmethod
    def get_feature(cls, feature_name: str) -> Any:
        """Get an enterprise feature if available."""
        if not cls.is_available(feature_name):
            raise EnterpriseFeatureRequired(feature_name)
        return cls._enterprise_features[feature_name]


# =============================================================================
# Generic Enterprise Stub - Single entry point for all enterprise features
# =============================================================================

class EnterpriseStub:
    """Generic stub for enterprise features.
    
    Provides a clean interface for accessing enterprise functionality
    without exposing specific feature names or implementation details.
    """
    
    @EnterpriseFeature()
    def execute(self, *args, **kwargs):
        """Execute an enterprise operation - requires enterprise."""
        pass
    
    @staticmethod
    def get_info() -> dict:
        """Get information about enterprise availability."""
        return {
            "available": EnterpriseFeature.is_available(),
            "upgrade_url": "https://wetail.co/enterprise",
            "documentation": "https://docs.wetail.co/enterprise",
        }
    
    def __getattr__(self, name: str):
        """Catch-all for any enterprise feature access."""
        def method(*args, **kwargs):
            if not EnterpriseFeature.is_available():
                raise EnterpriseFeatureRequired(name)
            # Delegate to enterprise package
            import wetail_enterprise
            feature = getattr(wetail_enterprise, name, None)
            if feature is None:
                raise AttributeError(f"Enterprise feature '{name}' not found")
            if callable(feature):
                return feature(*args, **kwargs)
            return feature
        return method


# Single export for enterprise features
enterprise = EnterpriseStub()
