"""
CDN cache utilities for LightWave CMS.

Handles caching content to S3/CDN as JSON for fast frontend consumption.
"""

import json
import logging

from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class CMSCache:
    """
    CDN cache management for CMS content.

    Caches pages, navigation, and components as JSON files
    to the configured S3 bucket (cdn.lightwave-media.ltd).
    """

    def __init__(self):
        self.base_path = getattr(settings, "LIGHTWAVE_CMS_CACHE_PATH", "cms")
        self._storage = None

    @property
    def storage(self):
        """Lazy-load storage backend."""
        if self._storage is None:
            try:
                from lightwave.storage import PublicMediaStorage

                self._storage = PublicMediaStorage()
            except ImportError:
                logger.warning("PublicMediaStorage not available, caching disabled")
                self._storage = False
        return self._storage

    def _save_json(self, path, data):
        """Save JSON data to storage."""
        if not self.storage:
            logger.debug(f"Cache disabled, skipping: {path}")
            return False

        try:
            content = json.dumps(data, indent=2, default=str)
            self.storage.save(path, ContentFile(content.encode("utf-8")))
            logger.info(f"Cached: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache {path}: {e}")
            return False

    def _delete(self, path):
        """Delete a file from storage."""
        if not self.storage:
            return False

        try:
            if self.storage.exists(path):
                self.storage.delete(path)
                logger.info(f"Invalidated: {path}")
                return True
        except Exception as e:
            logger.error(f"Failed to invalidate {path}: {e}")
        return False

    def _get_page_path(self, page):
        """Get the cache path for a page."""
        # Remove trailing slash for filename, handle root
        page_path = page.path.rstrip("/") or "index"
        if page_path.startswith("/"):
            page_path = page_path[1:]
        if not page_path:
            page_path = "index"
        return f"{self.base_path}/pages/{page.site.domain}/{page_path}.json"

    def cache_page(self, page):
        """
        Cache a page to CDN as JSON.

        Args:
            page: Page model instance
        """
        from .serializers import create_page_serializer

        PageSerializer = create_page_serializer(type(page), include_children=True)
        data = PageSerializer(page).data

        path = self._get_page_path(page)
        return self._save_json(path, data)

    def invalidate_page(self, page):
        """
        Remove a page from CDN cache.

        Args:
            page: Page model instance
        """
        path = self._get_page_path(page)
        return self._delete(path)

    def cache_navigation(self, site, location):
        """
        Cache a navigation menu to CDN.

        Args:
            site: Site model instance
            location: Menu location string (e.g., "main", "footer")
        """
        from .serializers import create_nav_item_serializer

        # Get the NavItem model from the site's related manager
        try:
            nav_items = site.nav_items.filter(
                menu_location=location,
                is_active=True,
                parent__isnull=True,
            ).order_by("order")

            if not nav_items.exists():
                return False

            NavItemSerializer = create_nav_item_serializer(type(nav_items.first()))
            data = NavItemSerializer(nav_items, many=True).data

            path = f"{self.base_path}/navigation/{site.domain}/{location}.json"
            return self._save_json(path, data)
        except Exception as e:
            logger.error(f"Failed to cache navigation: {e}")
            return False

    def cache_component(self, component):
        """
        Cache a component to CDN as JSON.

        Args:
            component: Component model instance
        """
        from .serializers import create_component_serializer

        ComponentSerializer = create_component_serializer(type(component))
        data = ComponentSerializer(component).data

        # Use slugified name for filename
        from django.utils.text import slugify

        name_slug = slugify(component.name)
        path = f"{self.base_path}/components/{component.site.domain}/{name_slug}.json"
        return self._save_json(path, data)

    def cache_site(self, site):
        """
        Cache site configuration to CDN.

        Args:
            site: Site model instance
        """
        from .serializers import create_site_serializer

        SiteSerializer = create_site_serializer(type(site))
        data = SiteSerializer(site).data

        path = f"{self.base_path}/sites/{site.domain}.json"
        return self._save_json(path, data)

    def sync_all(self, site=None):
        """
        Sync all content to CDN.

        Args:
            site: Optional Site instance to limit sync scope

        Returns:
            dict with counts of cached items
        """
        counts = {"sites": 0, "pages": 0, "navigation": 0, "components": 0}

        # This requires concrete models, so it should be called from
        # project code with access to the models
        logger.warning("sync_all should be called from project code with concrete models")
        return counts
