"""
Security Middleware

Provides essential security headers and rate limiting.

Licensed under Apache License 2.0
Copyright (c) 2024-2025 Wetail Technologies
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add security headers to all responses.
    
    Adds headers like:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Content-Security-Policy (basic)
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        # Security header configuration
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }
        # Optional CSP header
        csp = getattr(settings, 'CONTENT_SECURITY_POLICY', None)
        if csp:
            self.headers['Content-Security-Policy'] = csp

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # Add security headers
        for header, value in self.headers.items():
            if header not in response:
                response[header] = value
        
        return response


class RateLimitMiddleware:
    """Simple in-memory rate limiting middleware.
    
    Configuration in settings.py:
        RATE_LIMIT_REQUESTS = 100  # requests
        RATE_LIMIT_WINDOW = 60     # seconds
        RATE_LIMIT_PATHS = ['/api/', '/login/']  # paths to rate limit
    
    For production, use Redis-backed rate limiting instead.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        # Configuration
        self.requests_limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.window_seconds = getattr(settings, 'RATE_LIMIT_WINDOW', 60)
        self.paths = getattr(settings, 'RATE_LIMIT_PATHS', ['/api/'])
        # In-memory storage (use Redis in production)
        self._request_counts: Dict[str, list] = defaultdict(list)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Check if path should be rate limited
        if not self._should_rate_limit(request.path):
            return self.get_response(request)

        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if self._is_rate_limited(client_id):
            logger.warning(f"Rate limit exceeded for {client_id}")
            return HttpResponseForbidden(
                "Rate limit exceeded. Please try again later.",
                content_type='text/plain'
            )

        # Record request
        self._record_request(client_id)
        
        return self.get_response(request)

    def _should_rate_limit(self, path: str) -> bool:
        """Check if path should be rate limited."""
        return any(path.startswith(p) for p in self.paths)

    def _get_client_id(self, request: HttpRequest) -> str:
        """Get unique client identifier from request."""
        # Try X-Forwarded-For first (for proxied requests)
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old entries and count recent requests
        self._request_counts[client_id] = [
            ts for ts in self._request_counts[client_id] 
            if ts > cutoff
        ]
        
        return len(self._request_counts[client_id]) >= self.requests_limit

    def _record_request(self, client_id: str) -> None:
        """Record a request timestamp for client."""
        self._request_counts[client_id].append(time.time())
