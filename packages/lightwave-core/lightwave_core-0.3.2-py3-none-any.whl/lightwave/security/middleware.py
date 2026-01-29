"""Security headers middleware for Django applications.

This middleware adds security headers to all responses to protect against
common web vulnerabilities like XSS, clickjacking, and MIME-type attacks.

Usage:
    Add to MIDDLEWARE in settings.py:
        MIDDLEWARE = [
            ...
            'lightwave.security.SecurityHeadersMiddleware',
            ...
        ]

    Configure via settings.py (all optional):
        LIGHTWAVE_SECURITY = {
            'HSTS_SECONDS': 31536000,  # 1 year
            'HSTS_INCLUDE_SUBDOMAINS': True,
            'HSTS_PRELOAD': True,
            'CONTENT_SECURITY_POLICY': "default-src 'self'; ...",
            'PERMISSIONS_POLICY': "geolocation=(), microphone=()",
            'REFERRER_POLICY': 'strict-origin-when-cross-origin',
            'X_FRAME_OPTIONS': 'DENY',
        }
"""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """Middleware that adds security headers to HTTP responses.

    Security headers included:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy

    All headers are configurable via Django settings.
    """

    # Default security configuration
    DEFAULT_CONFIG = {
        # HSTS: Force HTTPS for 1 year
        "HSTS_SECONDS": 31536000,
        "HSTS_INCLUDE_SUBDOMAINS": True,
        "HSTS_PRELOAD": True,
        # Content Security Policy
        "CONTENT_SECURITY_POLICY": None,  # Must be configured per-project
        # Frame options
        "X_FRAME_OPTIONS": "DENY",
        # Referrer policy
        "REFERRER_POLICY": "strict-origin-when-cross-origin",
        # Permissions policy (formerly Feature-Policy)
        "PERMISSIONS_POLICY": (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        ),
        # Enable/disable specific headers
        "ENABLE_HSTS": True,
        "ENABLE_CSP": True,
        "ENABLE_XSS_PROTECTION": True,
        "ENABLE_CONTENT_TYPE_OPTIONS": True,
        "ENABLE_FRAME_OPTIONS": True,
        "ENABLE_REFERRER_POLICY": True,
        "ENABLE_PERMISSIONS_POLICY": True,
    }

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load security configuration from Django settings.

        Returns:
            Merged configuration with defaults.
        """
        user_config = getattr(settings, "LIGHTWAVE_SECURITY", {})
        config = self.DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and add security headers to the response.

        Args:
            request: The HTTP request.

        Returns:
            The HTTP response with security headers added.
        """
        response = self.get_response(request)
        self._add_security_headers(request, response)
        return response

    def _add_security_headers(self, request: HttpRequest, response: HttpResponse) -> None:
        """Add all security headers to the response.

        Args:
            request: The HTTP request.
            response: The HTTP response to modify.
        """
        # Strict-Transport-Security (HSTS)
        if self.config["ENABLE_HSTS"] and request.is_secure():
            hsts_value = f"max-age={self.config['HSTS_SECONDS']}"
            if self.config["HSTS_INCLUDE_SUBDOMAINS"]:
                hsts_value += "; includeSubDomains"
            if self.config["HSTS_PRELOAD"]:
                hsts_value += "; preload"
            response["Strict-Transport-Security"] = hsts_value

        # Content-Security-Policy
        if self.config["ENABLE_CSP"] and self.config["CONTENT_SECURITY_POLICY"]:
            response["Content-Security-Policy"] = self.config["CONTENT_SECURITY_POLICY"]

        # X-Frame-Options
        if self.config["ENABLE_FRAME_OPTIONS"]:
            response["X-Frame-Options"] = self.config["X_FRAME_OPTIONS"]

        # X-Content-Type-Options
        if self.config["ENABLE_CONTENT_TYPE_OPTIONS"]:
            response["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (legacy, but still useful for older browsers)
        if self.config["ENABLE_XSS_PROTECTION"]:
            response["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        if self.config["ENABLE_REFERRER_POLICY"]:
            response["Referrer-Policy"] = self.config["REFERRER_POLICY"]

        # Permissions-Policy
        if self.config["ENABLE_PERMISSIONS_POLICY"]:
            response["Permissions-Policy"] = self.config["PERMISSIONS_POLICY"]


def get_csp_for_django_admin() -> str:
    """Get a Content-Security-Policy suitable for Django admin.

    Returns:
        CSP string that allows Django admin to function properly.
    """
    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "frame-ancestors 'none';"
    )


def get_strict_csp(
    *,
    script_src: str = "'self'",
    style_src: str = "'self'",
    img_src: str = "'self'",
    font_src: str = "'self'",
    connect_src: str = "'self'",
    frame_src: str = "'none'",
    object_src: str = "'none'",
    base_uri: str = "'self'",
    form_action: str = "'self'",
    report_uri: str | None = None,
) -> str:
    """Build a strict Content-Security-Policy.

    Args:
        script_src: Allowed sources for scripts.
        style_src: Allowed sources for stylesheets.
        img_src: Allowed sources for images.
        font_src: Allowed sources for fonts.
        connect_src: Allowed sources for fetch/XHR/WebSocket.
        frame_src: Allowed sources for frames.
        object_src: Allowed sources for plugins.
        base_uri: Allowed base URIs.
        form_action: Allowed form action URLs.
        report_uri: Optional URI to report CSP violations.

    Returns:
        A Content-Security-Policy string.
    """
    directives = [
        "default-src 'self'",
        f"script-src {script_src}",
        f"style-src {style_src}",
        f"img-src {img_src}",
        f"font-src {font_src}",
        f"connect-src {connect_src}",
        f"frame-src {frame_src}",
        f"object-src {object_src}",
        f"base-uri {base_uri}",
        f"form-action {form_action}",
        "frame-ancestors 'none'",
    ]

    if report_uri:
        directives.append(f"report-uri {report_uri}")

    return "; ".join(directives) + ";"
