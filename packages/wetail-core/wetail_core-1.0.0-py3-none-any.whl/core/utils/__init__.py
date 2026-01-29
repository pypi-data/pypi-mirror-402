"""
Wetail Core Utilities

Common utility functions and classes for the Wetail platform.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

from wetail_core.core.utils.caching import (
    CacheManager,
    cache_result,
    cache_queryset,
)

__all__ = [
    "CacheManager",
    "cache_result",
    "cache_queryset",
]
