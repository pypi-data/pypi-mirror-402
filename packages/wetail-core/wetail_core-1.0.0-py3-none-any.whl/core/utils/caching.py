"""
Caching Utilities

Provides caching decorators and utilities for performance optimization.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

import hashlib
from functools import wraps

from django.core.cache import cache


class CacheManager:
    """Comprehensive caching utility for performance optimization."""

    # Cache timeouts (in seconds)
    CACHE_TIMEOUTS = {
        'short': 300,      # 5 minutes
        'medium': 1800,    # 30 minutes
        'long': 3600,      # 1 hour
        'daily': 86400,    # 24 hours
    }

    @staticmethod
    def cache_key(prefix, *args, **kwargs):
        """Generate a consistent cache key.

        Note: Uses MD5 for cache key generation only (not for security).
        """
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    @staticmethod
    def get_or_set(key, callable_func, timeout='medium'):
        """Get from cache or set if not exists."""
        cached_value = cache.get(key)
        if cached_value is not None:
            return cached_value

        value = callable_func()
        cache_timeout = CacheManager.CACHE_TIMEOUTS.get(timeout, 1800)
        cache.set(key, value, cache_timeout)
        return value

    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate cache keys matching pattern.
        
        Note: Requires a cache backend that supports pattern deletion.
        For Redis: cache.delete_pattern(pattern)
        """
        pass


def cache_result(timeout='medium', key_prefix=None):
    """Decorator to cache function results.
    
    Args:
        timeout: Cache timeout level ('short', 'medium', 'long', 'daily')
        key_prefix: Optional custom prefix for cache key
        
    Example:
        @cache_result(timeout='long')
        def expensive_calculation(x, y):
            return x ** y
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            cache_key = CacheManager.cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = CacheManager.CACHE_TIMEOUTS.get(timeout, 1800)
            cache.set(cache_key, result, cache_timeout)

            return result
        return wrapper
    return decorator


def cache_queryset(timeout='medium'):
    """Cache QuerySet results.
    
    Note: Converts QuerySet to list for caching. Use carefully with large datasets.
    
    Args:
        timeout: Cache timeout level
        
    Example:
        @cache_queryset(timeout='medium')
        def get_active_products():
            return Product.objects.filter(is_active=True)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function and arguments
            cache_key = CacheManager.cache_key(
                f"queryset_{func.__name__}",
                *args,
                **kwargs
            )

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute query and cache
            queryset = func(*args, **kwargs)
            # Convert to list to cache the actual data
            result = list(queryset) if hasattr(queryset, '__iter__') else queryset

            cache_timeout = CacheManager.CACHE_TIMEOUTS.get(timeout, 1800)
            cache.set(cache_key, result, cache_timeout)

            return result
        return wrapper
    return decorator
