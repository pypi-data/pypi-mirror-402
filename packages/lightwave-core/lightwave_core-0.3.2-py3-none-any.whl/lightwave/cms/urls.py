"""
URL router configuration for LightWave CMS API.

This module provides a function to create URL patterns for CMS endpoints.
Projects should call create_cms_urls() with their concrete models.
"""

from rest_framework.routers import DefaultRouter


def create_cms_urls(
    site_viewset=None,
    page_viewset=None,
    block_viewset=None,
    nav_item_viewset=None,
    component_viewset=None,
    prefix="api/cms",
):
    """
    Create URL patterns for CMS API endpoints.

    Args:
        site_viewset: ViewSet for Site model
        page_viewset: ViewSet for Page model
        block_viewset: ViewSet for Block model
        nav_item_viewset: ViewSet for NavItem model
        component_viewset: ViewSet for Component model
        prefix: URL prefix (default: "api/cms")

    Returns:
        List of URL patterns

    Usage in urls.py:
        from lightwave.cms.urls import create_cms_urls
        from apps.content.views import (
            SiteViewSet, PageViewSet, BlockViewSet,
            NavItemViewSet, ComponentViewSet
        )

        cms_urls = create_cms_urls(
            site_viewset=SiteViewSet,
            page_viewset=PageViewSet,
            block_viewset=BlockViewSet,
            nav_item_viewset=NavItemViewSet,
            component_viewset=ComponentViewSet,
        )

        urlpatterns = [
            ...
            path("", include(cms_urls)),
        ]
    """
    router = DefaultRouter()

    if site_viewset:
        router.register(f"{prefix}/sites", site_viewset, basename="cms-site")

    if page_viewset:
        router.register(f"{prefix}/pages", page_viewset, basename="cms-page")

    if block_viewset:
        router.register(f"{prefix}/blocks", block_viewset, basename="cms-block")

    if nav_item_viewset:
        router.register(f"{prefix}/navigation", nav_item_viewset, basename="cms-nav")

    if component_viewset:
        router.register(f"{prefix}/components", component_viewset, basename="cms-component")

    return router.urls
