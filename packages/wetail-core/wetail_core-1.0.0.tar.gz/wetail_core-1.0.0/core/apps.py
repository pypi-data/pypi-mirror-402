"""
Core App Configuration

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the Wetail Core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wetail_core.core'
    label = 'wetail_core'
    verbose_name = 'Wetail Core'

    def ready(self):
        """Perform app initialization."""
        pass  # Signal imports would go here if needed
