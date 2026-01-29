"""
DRF serializers for LightWave CMS.

Uses factory functions to create serializers for concrete models,
following the pattern established in lightwave.auth.serializers.
"""

from rest_framework import serializers


def create_site_serializer(site_model):
    """
    Factory function to create a Site serializer.

    Usage:
        from apps.content.models import Site
        SiteSerializer = create_site_serializer(Site)
    """

    class SiteSerializer(serializers.ModelSerializer):
        class Meta:
            model = site_model
            fields = [
                "id",
                "domain",
                "name",
                "is_active",
                "settings",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["created_at", "updated_at"]

    return SiteSerializer


def create_block_serializer(block_model):
    """
    Factory function to create a Block serializer.

    Usage:
        from apps.content.models import Block
        BlockSerializer = create_block_serializer(Block)
    """

    class BlockSerializer(serializers.ModelSerializer):
        class Meta:
            model = block_model
            fields = [
                "id",
                "site",
                "block_type",
                "name",
                "props",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["created_at", "updated_at"]

    return BlockSerializer


def create_page_serializer(page_model, include_children=False):
    """
    Factory function to create a Page serializer.

    Args:
        page_model: The concrete Page model class
        include_children: Whether to include nested children

    Usage:
        from apps.content.models import Page
        PageSerializer = create_page_serializer(Page)
    """

    class PageSerializer(serializers.ModelSerializer):
        url = serializers.SerializerMethodField()
        children = serializers.SerializerMethodField() if include_children else None

        class Meta:
            model = page_model
            fields = [
                "id",
                "site",
                "parent",
                "title",
                "slug",
                "path",
                "depth",
                "page_type",
                "body",
                "metadata",
                "is_published",
                "published_at",
                "url",
                "created_at",
                "updated_at",
            ]
            if include_children:
                fields.append("children")
            read_only_fields = ["path", "depth", "created_at", "updated_at"]

        def get_url(self, obj):
            return obj.get_url()

        def get_children(self, obj):
            if not include_children:
                return None
            try:
                children = obj.get_children().filter(is_published=True)
                return PageListSerializer(children, many=True).data
            except (AttributeError, NotImplementedError):
                return []

    # Remove None fields
    if not include_children:
        PageSerializer.Meta.fields = [f for f in PageSerializer.Meta.fields if f != "children"]
        delattr(PageSerializer, "children")

    return PageSerializer


class PageListSerializer(serializers.Serializer):
    """Lightweight serializer for page lists (no body content)."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.CharField()
    path = serializers.CharField()
    page_type = serializers.CharField()
    is_published = serializers.BooleanField()
    published_at = serializers.DateTimeField()


def create_nav_item_serializer(nav_item_model):
    """
    Factory function to create a NavItem serializer.

    Usage:
        from apps.content.models import NavItem
        NavItemSerializer = create_nav_item_serializer(NavItem)
    """

    class NavItemSerializer(serializers.ModelSerializer):
        url = serializers.SerializerMethodField()
        children = serializers.SerializerMethodField()

        class Meta:
            model = nav_item_model
            fields = [
                "id",
                "site",
                "parent",
                "menu_location",
                "label",
                "url",
                "page",
                "order",
                "is_active",
                "css_class",
                "open_in_new_tab",
                "children",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["created_at", "updated_at"]

        def get_url(self, obj):
            return obj.get_url()

        def get_children(self, obj):
            if hasattr(obj, "children"):
                children = obj.children.filter(is_active=True).order_by("order")
                return NavItemSerializer(children, many=True).data
            return []

    return NavItemSerializer


def create_component_serializer(component_model):
    """
    Factory function to create a Component serializer.

    Usage:
        from apps.content.models import Component
        ComponentSerializer = create_component_serializer(Component)
    """

    class ComponentSerializer(serializers.ModelSerializer):
        class Meta:
            model = component_model
            fields = [
                "id",
                "site",
                "name",
                "component_type",
                "props",
                "is_global",
                "created_at",
                "updated_at",
            ]
            read_only_fields = ["created_at", "updated_at"]

    return ComponentSerializer
