"""
Site lookup middleware for multi-domain support.

This middleware attaches the current Site object to the request based on
the domain from the Host header. This enables the stampable multi-domain
architecture where the same codebase serves different sites.

Usage:
    Add to MIDDLEWARE in settings.py (before context processors run):
        MIDDLEWARE = [
            ...
            'lightwave.islands.middleware.SiteMiddleware',
            ...
        ]

    Configure the domain pointer in settings.py:
        from lightwave.islands.config import load_lightwave_config
        LIGHTWAVE_CONFIG = load_lightwave_config(BASE_DIR / "lightwave-config.yaml")
        # lightwave-config.yaml only needs: domain: "lightwave-media.site"

    Or specify domain directly:
        LIGHTWAVE_CONFIG = {"domain": "lightwave-media.site"}
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse

if TYPE_CHECKING:
    from lightwave.cms.models import BaseSite

logger = logging.getLogger(__name__)


class SiteMiddleware:
    """
    Attach Site to request based on domain.

    In production, looks up Site by the Host header domain.
    In development (DEBUG=True), uses the domain from LIGHTWAVE_CONFIG
    to support local development without matching hostnames.

    The Site object is attached to request.site and can be accessed
    by views and context processors.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self._site_model = None

    def _get_site_model(self):
        """Lazy load the Site model to avoid import issues at startup."""
        if self._site_model is None:
            try:
                from apps.cms.models import Site

                self._site_model = Site
            except ImportError:
                logger.warning(
                    "Could not import apps.cms.models.Site. " "SiteMiddleware requires a concrete Site model."
                )
                self._site_model = False  # Mark as unavailable
        return self._site_model if self._site_model else None

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Get the Site model
        Site = self._get_site_model()
        if not Site:
            # No Site model available, skip middleware
            return self.get_response(request)

        # Determine domain to look up
        domain = self._get_domain(request)

        try:
            request.site = Site.objects.get(domain=domain, is_active=True)
        except Site.DoesNotExist:
            # In DEBUG mode, try to find any active site as fallback
            if settings.DEBUG:
                fallback = Site.objects.filter(is_active=True).first()
                if fallback:
                    logger.debug(f"Site '{domain}' not found, using fallback: {fallback.domain}")
                    request.site = fallback
                else:
                    logger.warning("No active sites found. Create one in admin.")
                    request.site = None
            else:
                logger.error(f"Site not configured: {domain}")
                raise Http404(f"Site not configured: {domain}") from None

        return self.get_response(request)

    def _get_domain(self, request: HttpRequest) -> str:
        """
        Get the domain to look up.

        In DEBUG mode, uses LIGHTWAVE_CONFIG.domain to support local development.
        In production, uses the Host header (without port).
        """
        if settings.DEBUG:
            config = getattr(settings, "LIGHTWAVE_CONFIG", {})
            config_domain = config.get("domain")
            if config_domain:
                return config_domain

        # Get from Host header, strip port if present
        host = request.get_host()
        return host.split(":")[0]


def get_current_site(request: HttpRequest) -> "BaseSite | None":
    """
    Get the current Site from the request.

    This is a convenience function for use in views and context processors.

    Args:
        request: The HTTP request (must have been processed by SiteMiddleware)

    Returns:
        The Site object or None if not available
    """
    return getattr(request, "site", None)
