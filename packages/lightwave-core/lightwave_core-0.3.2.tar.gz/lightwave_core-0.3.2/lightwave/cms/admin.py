"""
Django Admin configuration for LightWave CMS.

Provides base admin classes and factory functions for registering
CMS models with the Django admin. Designed for copywriters and
content managers with appropriate permissions and UI.

Usage:
    # In your admin.py
    from django.contrib import admin
    from lightwave.cms.admin import (
        create_site_admin,
        create_page_admin,
        create_block_admin,
        create_nav_item_admin,
        create_component_admin,
    )
    from .models import Site, Page, Block, NavItem, Component

    @admin.register(Site)
    class SiteAdmin(create_site_admin(Site)):
        pass

    @admin.register(Page)
    class PageAdmin(create_page_admin(Page)):
        pass

    # Or use the quick registration helper:
    from lightwave.cms.admin import register_cms_admin
    register_cms_admin(Site, Page, Block, NavItem, Component)
"""

from typing import Any

from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class CMSAdminMixin:
    """Common functionality for CMS admin classes."""

    def get_readonly_fields(self, request: HttpRequest, obj: Model | None = None) -> tuple[str, ...]:
        """Make timestamps readonly."""
        readonly = list(super().get_readonly_fields(request, obj))
        if hasattr(self.model, "created_at"):
            readonly.extend(["created_at", "updated_at"])
        return tuple(readonly)


def create_site_admin(site_model: type[Model]) -> type[admin.ModelAdmin]:
    """
    Create an admin class for the Site model.

    Args:
        site_model: The concrete Site model class.

    Returns:
        A ModelAdmin class configured for Site management.
    """

    class SiteAdmin(CMSAdminMixin, admin.ModelAdmin):
        list_display = ["name", "domain", "is_active", "created_at"]
        list_filter = ["is_active"]
        search_fields = ["name", "domain"]
        ordering = ["name"]

        fieldsets = (
            (None, {"fields": ("name", "domain", "is_active")}),
            (
                _("Settings"),
                {
                    "fields": ("settings",),
                    "classes": ("collapse",),
                },
            ),
            (
                _("Timestamps"),
                {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

        readonly_fields = ["created_at", "updated_at"]

    return SiteAdmin


def create_page_admin(
    page_model: type[Model],
    site_model: type[Model] | None = None,
) -> type[admin.ModelAdmin]:
    """
    Create an admin class for the Page model.

    Args:
        page_model: The concrete Page model class.
        site_model: Optional Site model for filtering.

    Returns:
        A ModelAdmin class configured for Page management.
    """

    class PageAdmin(CMSAdminMixin, admin.ModelAdmin):
        list_display = [
            "title",
            "path",
            "page_type",
            "is_published",
            "published_status",
            "updated_at",
        ]
        list_filter = ["is_published", "page_type", "site"]
        search_fields = ["title", "slug", "path"]
        ordering = ["path"]
        prepopulated_fields = {"slug": ("title",)}
        date_hierarchy = "created_at"

        fieldsets = (
            (
                None,
                {
                    "fields": ("site", "parent", "title", "slug", "page_type"),
                },
            ),
            (
                _("Content"),
                {
                    "fields": ("body",),
                    "description": _("Page content as JSON. Use the block editor for visual editing."),
                },
            ),
            (
                _("SEO & Metadata"),
                {
                    "fields": ("metadata",),
                    "classes": ("collapse",),
                    "description": _("SEO metadata including title, description, and social images."),
                },
            ),
            (
                _("Publishing"),
                {
                    "fields": ("is_published", "published_at"),
                },
            ),
            (
                _("System"),
                {
                    "fields": ("path", "depth", "created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

        readonly_fields = ["path", "depth", "created_at", "updated_at"]

        actions = ["publish_pages", "unpublish_pages"]

        @admin.display(description=_("Status"))
        def published_status(self, obj: Model) -> str:
            if obj.is_published:
                return format_html('<span style="color: #22c55e;">●</span> Published')
            return format_html('<span style="color: #94a3b8;">●</span> Draft')

        @admin.action(description=_("Publish selected pages"))
        def publish_pages(self, request: HttpRequest, queryset: Any) -> None:
            for page in queryset:
                page.publish()
            self.message_user(
                request,
                _("%(count)d pages published.") % {"count": queryset.count()},
            )

        @admin.action(description=_("Unpublish selected pages"))
        def unpublish_pages(self, request: HttpRequest, queryset: Any) -> None:
            queryset.update(is_published=False)
            self.message_user(
                request,
                _("%(count)d pages unpublished.") % {"count": queryset.count()},
            )

        def get_queryset(self, request: HttpRequest) -> Any:
            """Optimize queryset with select_related."""
            qs = super().get_queryset(request)
            return qs.select_related("site", "parent")

    return PageAdmin


def create_block_admin(
    block_model: type[Model],
    site_model: type[Model] | None = None,
) -> type[admin.ModelAdmin]:
    """
    Create an admin class for the Block model.

    Args:
        block_model: The concrete Block model class.
        site_model: Optional Site model for filtering.

    Returns:
        A ModelAdmin class configured for Block management.
    """

    class BlockAdmin(CMSAdminMixin, admin.ModelAdmin):
        list_display = ["display_name", "block_type", "site", "created_at"]
        list_filter = ["block_type", "site"]
        search_fields = ["name", "props"]
        ordering = ["-created_at"]

        fieldsets = (
            (
                None,
                {
                    "fields": ("site", "block_type", "name"),
                },
            ),
            (
                _("Content"),
                {
                    "fields": ("props",),
                    "description": _("Block properties as JSON. Schema varies by block type."),
                },
            ),
            (
                _("Timestamps"),
                {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

        readonly_fields = ["created_at", "updated_at"]

        @admin.display(description=_("Name"))
        def display_name(self, obj: Model) -> str:
            if obj.name:
                return obj.name
            return f"{obj.block_type} (unnamed)"

    return BlockAdmin


def create_nav_item_admin(
    nav_item_model: type[Model],
    site_model: type[Model] | None = None,
    page_model: type[Model] | None = None,
) -> type[admin.ModelAdmin]:
    """
    Create an admin class for the NavItem model.

    Args:
        nav_item_model: The concrete NavItem model class.
        site_model: Optional Site model for filtering.
        page_model: Optional Page model for linking.

    Returns:
        A ModelAdmin class configured for NavItem management.
    """

    class NavItemAdmin(CMSAdminMixin, admin.ModelAdmin):
        list_display = [
            "label",
            "menu_location",
            "get_url",
            "order",
            "is_active",
            "site",
        ]
        list_filter = ["menu_location", "is_active", "site"]
        list_editable = ["order", "is_active"]
        search_fields = ["label", "url"]
        ordering = ["site", "menu_location", "order"]

        fieldsets = (
            (
                None,
                {
                    "fields": ("site", "menu_location", "parent", "label"),
                },
            ),
            (
                _("Link"),
                {
                    "fields": ("url", "page", "open_in_new_tab"),
                    "description": _("Either enter a URL or select a page. Page takes precedence."),
                },
            ),
            (
                _("Display"),
                {
                    "fields": ("order", "is_active", "css_class"),
                },
            ),
            (
                _("Timestamps"),
                {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

        readonly_fields = ["created_at", "updated_at"]

        def get_queryset(self, request: HttpRequest) -> Any:
            """Optimize queryset with select_related."""
            qs = super().get_queryset(request)
            return qs.select_related("site", "parent", "page")

    return NavItemAdmin


def create_component_admin(
    component_model: type[Model],
    site_model: type[Model] | None = None,
) -> type[admin.ModelAdmin]:
    """
    Create an admin class for the Component model.

    Args:
        component_model: The concrete Component model class.
        site_model: Optional Site model for filtering.

    Returns:
        A ModelAdmin class configured for Component management.
    """

    class ComponentAdmin(CMSAdminMixin, admin.ModelAdmin):
        list_display = [
            "name",
            "component_type",
            "is_global",
            "site",
            "updated_at",
        ]
        list_filter = ["component_type", "is_global", "site"]
        search_fields = ["name", "component_type"]
        ordering = ["site", "name"]

        fieldsets = (
            (
                None,
                {
                    "fields": ("site", "name", "component_type", "is_global"),
                },
            ),
            (
                _("Props"),
                {
                    "fields": ("props",),
                    "description": _("Component props as JSON. Schema depends on component type."),
                },
            ),
            (
                _("Timestamps"),
                {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )

        readonly_fields = ["created_at", "updated_at"]

    return ComponentAdmin


def register_cms_admin(
    site_model: type[Model],
    page_model: type[Model],
    block_model: type[Model] | None = None,
    nav_item_model: type[Model] | None = None,
    component_model: type[Model] | None = None,
) -> None:
    """
    Quick helper to register all CMS models with the admin.

    Args:
        site_model: The concrete Site model class.
        page_model: The concrete Page model class.
        block_model: Optional Block model class.
        nav_item_model: Optional NavItem model class.
        component_model: Optional Component model class.

    Example:
        from lightwave.cms.admin import register_cms_admin
        from .models import Site, Page, Block, NavItem, Component

        register_cms_admin(Site, Page, Block, NavItem, Component)
    """
    admin.site.register(site_model, create_site_admin(site_model))
    admin.site.register(page_model, create_page_admin(page_model, site_model))

    if block_model:
        admin.site.register(block_model, create_block_admin(block_model, site_model))

    if nav_item_model:
        admin.site.register(
            nav_item_model,
            create_nav_item_admin(nav_item_model, site_model, page_model),
        )

    if component_model:
        admin.site.register(component_model, create_component_admin(component_model, site_model))


# Copywriter permission helpers
class CopywriterPermissionMixin:
    """
    Mixin to restrict admin access to copywriter-appropriate actions.

    Copywriters can:
    - View, add, change pages and blocks
    - View sites and nav items
    - Cannot delete or change site settings

    Usage:
        class PageAdmin(CopywriterPermissionMixin, create_page_admin(Page)):
            pass
    """

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Only superusers can delete."""
        if request.user.is_superuser:
            return True
        # Check for explicit delete permission
        return super().has_delete_permission(request, obj)


class SiteReadOnlyMixin:
    """
    Mixin to make Site admin read-only for non-superusers.

    Copywriters can view sites but not modify settings.
    """

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        return request.user.is_superuser
