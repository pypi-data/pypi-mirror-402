"""
Enterprise Feature Stubs

Provides graceful handling for enterprise-only features in the core package.
When enterprise features are accessed without wetail-enterprise installed,
helpful error messages guide users to the enterprise package.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

from wetail_core.stubs.enterprise import (
    EnterpriseFeature,
    EnterpriseFeatureRequired,
    EnterpriseStub,
    enterprise,
)

__all__ = [
    "EnterpriseFeature",
    "EnterpriseFeatureRequired",
    "EnterpriseStub",
    "enterprise",
]
