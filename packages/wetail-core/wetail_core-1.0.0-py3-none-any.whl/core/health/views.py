"""
Health Check Views

Provides endpoints for Kubernetes/Docker health probes.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

import logging
from typing import Dict, Any

from django.http import JsonResponse, HttpRequest
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger(__name__)


def health_check(request: HttpRequest) -> JsonResponse:
    """Basic health check endpoint.
    
    Returns 200 if the application is running.
    Suitable for basic load balancer health checks.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'wetail-core',
    })


def liveness_check(request: HttpRequest) -> JsonResponse:
    """Kubernetes liveness probe endpoint.
    
    Returns 200 if the application process is alive.
    Should be fast and not depend on external services.
    """
    return JsonResponse({
        'status': 'alive',
    })


def readiness_check(request: HttpRequest) -> JsonResponse:
    """Kubernetes readiness probe endpoint.
    
    Checks if the application is ready to receive traffic.
    Verifies database and cache connectivity.
    """
    checks: Dict[str, Any] = {
        'database': False,
        'cache': False,
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks['database_error'] = str(e)
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['cache'] = True
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        checks['cache_error'] = str(e)
    
    # Determine overall status
    all_healthy = all(checks.get(k) for k in ['database', 'cache'])
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'ready' if all_healthy else 'not_ready',
        'checks': checks,
    }, status=status_code)


def detailed_health_check(request: HttpRequest) -> JsonResponse:
    """Detailed health check with system information.
    
    Note: This endpoint should be protected in production
    as it may expose sensitive system information.
    """
    import sys
    import django
    
    checks = {
        'database': False,
        'cache': False,
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = True
        checks['database_vendor'] = connection.vendor
    except Exception as e:
        checks['database_error'] = str(e)
    
    # Cache check
    try:
        cache.set('detailed_health_check', 'ok', 10)
        if cache.get('detailed_health_check') == 'ok':
            checks['cache'] = True
    except Exception as e:
        checks['cache_error'] = str(e)
    
    all_healthy = all(checks.get(k) for k in ['database', 'cache'])
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks,
        'versions': {
            'python': sys.version,
            'django': django.VERSION,
            'wetail_core': '1.0.0',
        },
    }, status=200 if all_healthy else 503)
