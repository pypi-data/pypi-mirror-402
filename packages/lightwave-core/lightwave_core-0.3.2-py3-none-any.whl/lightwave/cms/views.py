"""
DRF ViewSets for LightWave CMS.

Uses factory functions to create ViewSets for concrete models,
following the pattern established in other lightwave modules.
"""

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class CMSPermission(permissions.BasePermission):
    """
    Permission class for CMS operations.

    - Read operations: Public access for published content
    - Write operations: Staff only
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_staff


def create_site_viewset(site_model, site_serializer):
    """
    Factory function to create a Site ViewSet.

    Usage:
        from apps.content.models import Site
        SiteSerializer = create_site_serializer(Site)
        SiteViewSet = create_site_viewset(Site, SiteSerializer)
    """

    class SiteViewSet(viewsets.ModelViewSet):
        queryset = site_model.objects.all()
        serializer_class = site_serializer
        permission_classes = [CMSPermission]
        lookup_field = "domain"

        def get_queryset(self):
            qs = super().get_queryset()
            if not self.request.user.is_staff:
                qs = qs.filter(is_active=True)
            return qs

    return SiteViewSet


def create_page_viewset(page_model, page_serializer, page_list_serializer=None):
    """
    Factory function to create a Page ViewSet.

    Args:
        page_model: The concrete Page model class
        page_serializer: The page serializer class
        page_list_serializer: Optional lightweight serializer for lists

    Usage:
        from apps.content.models import Page
        PageSerializer = create_page_serializer(Page)
        PageViewSet = create_page_viewset(Page, PageSerializer)
    """

    class PageViewSet(viewsets.ModelViewSet):
        queryset = page_model.objects.all()
        serializer_class = page_serializer
        permission_classes = [CMSPermission]

        def get_queryset(self):
            qs = super().get_queryset()

            # Filter by site
            site = self.request.query_params.get("site")
            if site:
                qs = qs.filter(site__domain=site)

            # Filter by page_type
            page_type = self.request.query_params.get("page_type")
            if page_type:
                qs = qs.filter(page_type=page_type)

            # Filter by parent
            parent = self.request.query_params.get("parent")
            if parent == "null" or parent == "":
                qs = qs.filter(parent__isnull=True)
            elif parent:
                qs = qs.filter(parent_id=parent)

            # Non-staff only see published
            if not self.request.user.is_staff:
                qs = qs.filter(is_published=True)

            return qs.select_related("site", "parent")

        def get_serializer_class(self):
            if self.action == "list" and page_list_serializer:
                return page_list_serializer
            return self.serializer_class

        @action(detail=True, methods=["post"])
        def publish(self, request, pk=None):
            """Publish a page."""
            page = self.get_object()
            page.publish()
            serializer = self.get_serializer(page)
            return Response(serializer.data)

        @action(detail=True, methods=["post"])
        def unpublish(self, request, pk=None):
            """Unpublish a page."""
            page = self.get_object()
            page.unpublish()
            serializer = self.get_serializer(page)
            return Response(serializer.data)

        @action(detail=False, methods=["get"])
        def by_path(self, request):
            """
            Get a page by site domain and path.

            Query params:
                - site: Domain name (required)
                - path: Page path (default: "/")
            """
            site = request.query_params.get("site")
            path = request.query_params.get("path", "/")

            if not site:
                return Response(
                    {"error": "site parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Normalize path
            if not path.startswith("/"):
                path = "/" + path
            if not path.endswith("/"):
                path = path + "/"

            page = get_object_or_404(self.get_queryset(), site__domain=site, path=path)
            serializer = self.get_serializer(page)
            return Response(serializer.data)

    return PageViewSet


def create_block_viewset(block_model, block_serializer):
    """
    Factory function to create a Block ViewSet.

    Usage:
        from apps.content.models import Block
        BlockSerializer = create_block_serializer(Block)
        BlockViewSet = create_block_viewset(Block, BlockSerializer)
    """

    class BlockViewSet(viewsets.ModelViewSet):
        queryset = block_model.objects.all()
        serializer_class = block_serializer
        permission_classes = [CMSPermission]

        def get_queryset(self):
            qs = super().get_queryset()

            # Filter by site
            site = self.request.query_params.get("site")
            if site:
                qs = qs.filter(site__domain=site)

            # Filter by block_type
            block_type = self.request.query_params.get("block_type")
            if block_type:
                qs = qs.filter(block_type=block_type)

            # Filter by name (for reusable blocks)
            name = self.request.query_params.get("name")
            if name:
                qs = qs.filter(name__icontains=name)

            return qs.select_related("site")

    return BlockViewSet


def create_nav_item_viewset(nav_item_model, nav_item_serializer):
    """
    Factory function to create a NavItem ViewSet.

    Usage:
        from apps.content.models import NavItem
        NavItemSerializer = create_nav_item_serializer(NavItem)
        NavItemViewSet = create_nav_item_viewset(NavItem, NavItemSerializer)
    """

    class NavItemViewSet(viewsets.ModelViewSet):
        queryset = nav_item_model.objects.all()
        serializer_class = nav_item_serializer
        permission_classes = [CMSPermission]

        def get_queryset(self):
            qs = super().get_queryset()

            # Filter by site
            site = self.request.query_params.get("site")
            if site:
                qs = qs.filter(site__domain=site)

            # Filter by menu_location
            location = self.request.query_params.get("location")
            if location:
                qs = qs.filter(menu_location=location)

            # Only root items by default (children are nested)
            if self.action == "list":
                qs = qs.filter(parent__isnull=True)

            # Non-staff only see active
            if not self.request.user.is_staff:
                qs = qs.filter(is_active=True)

            return qs.select_related("site", "page").order_by("order")

        @action(
            detail=False,
            methods=["get"],
            url_path="menu/(?P<site>[^/]+)/(?P<location>[^/]+)",
        )
        def menu(self, request, site=None, location=None):
            """
            Get a complete navigation menu for a site and location.

            URL: /api/cms/navigation/menu/{site}/{location}/
            """
            qs = self.get_queryset().filter(
                site__domain=site,
                menu_location=location,
                parent__isnull=True,
            )
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)

    return NavItemViewSet


def create_component_viewset(component_model, component_serializer):
    """
    Factory function to create a Component ViewSet.

    Usage:
        from apps.content.models import Component
        ComponentSerializer = create_component_serializer(Component)
        ComponentViewSet = create_component_viewset(Component, ComponentSerializer)
    """

    class ComponentViewSet(viewsets.ModelViewSet):
        queryset = component_model.objects.all()
        serializer_class = component_serializer
        permission_classes = [CMSPermission]

        def get_queryset(self):
            qs = super().get_queryset()

            # Filter by site
            site = self.request.query_params.get("site")
            if site:
                qs = qs.filter(site__domain=site)

            # Filter by component_type
            component_type = self.request.query_params.get("component_type")
            if component_type:
                qs = qs.filter(component_type=component_type)

            # Filter by global
            is_global = self.request.query_params.get("global")
            if is_global is not None:
                qs = qs.filter(is_global=is_global.lower() == "true")

            return qs.select_related("site")

        @action(detail=False, methods=["get"])
        def by_name(self, request):
            """
            Get a component by site and name.

            Query params:
                - site: Domain name (required)
                - name: Component name (required)
            """
            site = request.query_params.get("site")
            name = request.query_params.get("name")

            if not site or not name:
                return Response(
                    {"error": "site and name parameters are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            component = get_object_or_404(self.get_queryset(), site__domain=site, name=name)
            serializer = self.get_serializer(component)
            return Response(serializer.data)

    return ComponentViewSet
