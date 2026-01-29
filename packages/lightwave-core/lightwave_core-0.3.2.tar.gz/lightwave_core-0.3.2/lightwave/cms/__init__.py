"""
LightWave CMS Module.

A lightweight, multi-domain CMS for LightWave projects.
Provides abstract models, API views, caching, and template tags
for managing content across multiple domains.

Usage:
    # In your models.py
    from lightwave.cms.models import BaseSite, BasePage, BaseBlock, BaseNavItem, BaseComponent

    class Site(BaseSite):
        pass

    class Page(BasePage):
        site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="pages")
        parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE)

    # In your views.py
    from lightwave.cms.serializers import create_page_serializer
    from lightwave.cms.views import create_page_viewset

    PageSerializer = create_page_serializer(Page)
    PageViewSet = create_page_viewset(Page, PageSerializer)

    # In your apps.py
    from lightwave.cms.signals import connect_cms_signals

    class ContentConfig(AppConfig):
        def ready(self):
            from .models import Page, NavItem, Component
            connect_cms_signals(Page, NavItem, Component)

    # In your templates
    {% load cms_tags %}
    {% render_page_body page %}
    {% cms_nav "main" as main_nav %}
"""

# Lazy imports to avoid AppRegistryNotReady errors
# All exports are available via __getattr__

__all__ = [
    # Models
    "BaseSite",
    "BasePage",
    "BaseBlock",
    "BaseNavItem",
    "BaseComponent",
    "BlockTypes",
    "PageTypes",
    # Serializers
    "create_site_serializer",
    "create_page_serializer",
    "create_block_serializer",
    "create_nav_item_serializer",
    "create_component_serializer",
    "PageListSerializer",
    # Views
    "CMSPermission",
    "create_site_viewset",
    "create_page_viewset",
    "create_block_viewset",
    "create_nav_item_viewset",
    "create_component_viewset",
    # URLs
    "create_cms_urls",
    # Signals
    "connect_cms_signals",
    # Cache
    "CMSCache",
    # Renderers
    "render_block",
    "render_blocks",
    "render_page_body",
]


def __getattr__(name):
    """Lazy import to avoid AppRegistryNotReady errors."""
    # Models
    if name in (
        "BaseSite",
        "BasePage",
        "BaseBlock",
        "BaseNavItem",
        "BaseComponent",
        "BlockTypes",
        "PageTypes",
    ):
        from lightwave.cms import models

        return getattr(models, name)

    # Serializers
    if name in (
        "create_site_serializer",
        "create_page_serializer",
        "create_block_serializer",
        "create_nav_item_serializer",
        "create_component_serializer",
        "PageListSerializer",
    ):
        from lightwave.cms import serializers

        return getattr(serializers, name)

    # Views
    if name in (
        "CMSPermission",
        "create_site_viewset",
        "create_page_viewset",
        "create_block_viewset",
        "create_nav_item_viewset",
        "create_component_viewset",
    ):
        from lightwave.cms import views

        return getattr(views, name)

    # URLs
    if name == "create_cms_urls":
        from lightwave.cms.urls import create_cms_urls

        return create_cms_urls

    # Signals
    if name == "connect_cms_signals":
        from lightwave.cms.signals import connect_cms_signals

        return connect_cms_signals

    # Cache
    if name == "CMSCache":
        from lightwave.cms.cache import CMSCache

        return CMSCache

    # Renderers
    if name in ("render_block", "render_blocks", "render_page_body"):
        from lightwave.cms import renderers

        return getattr(renderers, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
