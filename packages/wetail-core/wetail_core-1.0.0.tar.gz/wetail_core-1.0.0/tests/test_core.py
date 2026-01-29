"""
Wetail Core Unit Tests

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

import pytest


class TestWetailCoreImport:
    """Test that wetail_core package imports correctly."""

    def test_import_package(self):
        """Test basic package import."""
        import wetail_core
        assert wetail_core.__version__ == "1.0.0"
        assert wetail_core.__license__ == "Apache-2.0"

    def test_import_enterprise_feature(self):
        """Test EnterpriseFeature import."""
        from wetail_core import EnterpriseFeature
        assert EnterpriseFeature is not None

    def test_import_enterprise_stub(self):
        """Test enterprise stub import."""
        from wetail_core import enterprise
        assert enterprise is not None


class TestEnterpriseStub:
    """Test enterprise stub functionality."""

    def test_enterprise_stub_get_info(self):
        """Test enterprise stub get_info method."""
        from wetail_core.stubs.enterprise import EnterpriseStub
        
        stub = EnterpriseStub()
        info = stub.get_info()
        
        assert "available" in info
        assert "upgrade_url" in info
        assert info["available"] is False  # Enterprise not installed

    def test_enterprise_feature_not_available(self):
        """Test that EnterpriseFeature reports not available."""
        from wetail_core.stubs.enterprise import EnterpriseFeature
        
        # Should return False since wetail_enterprise is not installed
        assert EnterpriseFeature.is_available() is False

    def test_enterprise_feature_decorator(self):
        """Test EnterpriseFeature decorator raises exception."""
        from wetail_core.stubs.enterprise import (
            EnterpriseFeature,
            EnterpriseFeatureRequired,
        )

        @EnterpriseFeature("test_feature")
        def protected_function():
            return "success"

        with pytest.raises(EnterpriseFeatureRequired):
            protected_function()

    def test_enterprise_feature_with_fallback(self):
        """Test EnterpriseFeature decorator with fallback."""
        from wetail_core.stubs.enterprise import EnterpriseFeature

        @EnterpriseFeature("test_feature", fallback="fallback_value")
        def protected_function():
            return "success"

        result = protected_function()
        assert result == "fallback_value"


class TestCoreUtils:
    """Test core utility functions."""

    def test_import_caching(self):
        """Test caching utilities import."""
        from wetail_core.core.utils import caching
        assert hasattr(caching, "CacheManager")

    def test_import_error_handling(self):
        """Test error handling utilities import."""
        from wetail_core.core.utils import error_handling
        assert hasattr(error_handling, "safe_execute")

    def test_import_lazy_imports(self):
        """Test lazy imports utilities."""
        from wetail_core.core.utils import lazy_imports
        assert hasattr(lazy_imports, "LazyImport")


class TestCacheManager:
    """Test CacheManager functionality."""

    def test_cache_manager_init(self):
        """Test CacheManager initialization."""
        from wetail_core.core.utils.caching import CacheManager
        
        manager = CacheManager(prefix="test")
        assert manager.prefix == "test"

    def test_cache_manager_key_generation(self):
        """Test cache key generation."""
        from wetail_core.core.utils.caching import CacheManager
        
        manager = CacheManager(prefix="myapp")
        key = manager.make_key("user", "123")
        
        assert "myapp" in key
        assert "user" in key
        assert "123" in key


class TestHealthViews:
    """Test health check views."""

    def test_import_health_views(self):
        """Test health views import."""
        from wetail_core.core.health import views
        assert hasattr(views, "health_check")
        assert hasattr(views, "readiness_check")
        assert hasattr(views, "liveness_check")


class TestMiddleware:
    """Test middleware components."""

    def test_import_security_middleware(self):
        """Test security middleware import."""
        from wetail_core.core.middleware import security
        assert hasattr(security, "SecurityHeadersMiddleware")
