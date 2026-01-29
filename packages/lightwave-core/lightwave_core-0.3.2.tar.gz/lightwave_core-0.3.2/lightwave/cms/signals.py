"""
Signal handlers for LightWave CMS.

Handles automatic cache synchronization when content changes.
"""

from django.db.models.signals import post_delete, post_save


def _make_page_cache_handler(cache_instance):
    """Create a signal handler for caching pages on save."""

    def cache_page_on_save(sender, instance, created, **kwargs):
        """Cache published pages to CDN."""
        if instance.is_published:
            cache_instance.cache_page(instance)
        else:
            # Remove from cache if unpublished
            cache_instance.invalidate_page(instance)

    return cache_page_on_save


def _make_page_invalidate_handler(cache_instance):
    """Create a signal handler for invalidating pages on delete."""

    def invalidate_page_on_delete(sender, instance, **kwargs):
        """Remove page from CDN cache."""
        cache_instance.invalidate_page(instance)

    return invalidate_page_on_delete


def _make_nav_cache_handler(cache_instance):
    """Create a signal handler for caching navigation on save."""

    def cache_nav_on_save(sender, instance, created, **kwargs):
        """Cache navigation to CDN."""
        if instance.is_active:
            cache_instance.cache_navigation(instance.site, instance.menu_location)

    return cache_nav_on_save


def _make_component_cache_handler(cache_instance):
    """Create a signal handler for caching components on save."""

    def cache_component_on_save(sender, instance, created, **kwargs):
        """Cache component to CDN."""
        cache_instance.cache_component(instance)

    return cache_component_on_save


def connect_cms_signals(
    page_model=None,
    nav_item_model=None,
    component_model=None,
    cache_class=None,
):
    """
    Connect CMS signals for a project.

    This should be called in your app's AppConfig.ready() method.

    Args:
        page_model: Concrete Page model class
        nav_item_model: Concrete NavItem model class (optional)
        component_model: Concrete Component model class (optional)
        cache_class: Custom cache class (optional, defaults to CMSCache)

    Usage in apps.py:
        class ContentConfig(AppConfig):
            name = "apps.content"

            def ready(self):
                from lightwave.cms.signals import connect_cms_signals
                from apps.content.models import Page, NavItem, Component

                connect_cms_signals(
                    page_model=Page,
                    nav_item_model=NavItem,
                    component_model=Component,
                )
    """
    if cache_class is None:
        from .cache import CMSCache

        cache_class = CMSCache

    cache_instance = cache_class()

    if page_model:
        post_save.connect(
            _make_page_cache_handler(cache_instance),
            sender=page_model,
            dispatch_uid="cms_page_cache_save",
        )
        post_delete.connect(
            _make_page_invalidate_handler(cache_instance),
            sender=page_model,
            dispatch_uid="cms_page_cache_delete",
        )

    if nav_item_model:
        post_save.connect(
            _make_nav_cache_handler(cache_instance),
            sender=nav_item_model,
            dispatch_uid="cms_nav_cache_save",
        )

    if component_model:
        post_save.connect(
            _make_component_cache_handler(cache_instance),
            sender=component_model,
            dispatch_uid="cms_component_cache_save",
        )
