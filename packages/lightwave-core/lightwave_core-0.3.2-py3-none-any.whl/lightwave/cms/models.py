"""
Abstract base models for LightWave CMS.

These models are meant to be extended by concrete implementations
in each Django project. They provide the core CMS functionality
for multi-domain content management.
"""

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from lightwave.utils.models import BaseModel


class BlockTypes(models.TextChoices):
    """Available block types for content composition."""

    PARAGRAPH = "paragraph", _("Paragraph")
    HEADING = "heading", _("Heading")
    IMAGE = "image", _("Image")
    GALLERY = "gallery", _("Gallery")
    CAPTION = "caption", _("Caption")
    QUOTE = "quote", _("Quote")
    CODE = "code", _("Code Block")
    HTML = "html", _("Raw HTML")
    EMBED = "embed", _("Embed")
    DIVIDER = "divider", _("Divider")


class PageTypes(models.TextChoices):
    """Common page types."""

    CONTENT = "content", _("Content Page")
    BLOG = "blog", _("Blog Post")
    BLOG_INDEX = "blog-index", _("Blog Index")
    LANDING = "landing", _("Landing Page")
    PRODUCT = "product", _("Product Page")


class BaseSite(BaseModel):
    """
    Site configuration for multi-domain CMS.

    Each domain (cineos.io, joelschaeffer.com, etc.) gets one Site.

    The settings JSONField holds all domain-specific configuration:
    - brand: name, tagline, email, logos, social links
    - features: use_teams, use_subscriptions, use_social_login
    - auth: URLs, providers, flags
    - islands: header/footer variants
    - seo: title_suffix, og_image
    - theme: light_mode, dark_mode
    - navigation: header, footer nav items

    This enables the stampable multi-domain architecture where the same
    codebase serves different sites based on the Site record.
    """

    domain = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("Domain name (e.g., 'cineos.io')"),
    )
    name = models.CharField(
        max_length=100,
        help_text=_("Human-readable site name"),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this site is active"),
    )
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Site configuration JSON (brand, features, auth, islands, seo, theme, navigation)"),
    )

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name

    # Convenience properties for accessing settings sections

    @property
    def brand(self) -> dict:
        """Get brand settings (name, tagline, logos, etc.)."""
        return self.settings.get("brand", {})

    @property
    def features(self) -> dict:
        """Get feature flags (use_teams, use_subscriptions, etc.)."""
        return self.settings.get("features", {})

    @property
    def auth_config(self) -> dict:
        """Get auth configuration (URLs, providers, flags)."""
        return self.settings.get("auth", {})

    @property
    def islands_config(self) -> dict:
        """Get islands configuration (header/footer variants)."""
        return self.settings.get("islands", {})

    @property
    def seo_config(self) -> dict:
        """Get SEO defaults (title_suffix, og_image)."""
        return self.settings.get("seo", {})

    @property
    def theme_config(self) -> dict:
        """Get theme configuration (light_mode, dark_mode)."""
        return self.settings.get("theme", {})

    @property
    def navigation(self) -> dict:
        """Get navigation configuration (header, footer)."""
        return self.settings.get("navigation", {})

    # Convenience methods for common lookups

    def get_setting(self, path: str, default=None):
        """
        Get a nested setting by dot-notation path.

        Example:
            site.get_setting("brand.name")
            site.get_setting("features.use_teams", default=False)
        """
        keys = path.split(".")
        value = self.settings
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value

    def has_feature(self, feature_name: str) -> bool:
        """Check if a feature flag is enabled."""
        return self.features.get(feature_name, False)


class BasePage(BaseModel):
    """
    Abstract page model with parent/child hierarchy.

    Uses materialized path for efficient tree queries.
    The path is auto-generated from the slug hierarchy.
    """

    # Note: site and parent ForeignKeys must be defined in concrete model
    # because they reference concrete models

    title = models.CharField(
        max_length=255,
        help_text=_("Page title"),
    )
    slug = models.SlugField(
        max_length=255,
        help_text=_("URL slug for this page"),
    )
    path = models.CharField(
        max_length=1000,
        db_index=True,
        editable=False,
        help_text=_("Full path from root (auto-generated)"),
    )
    depth = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text=_("Depth in page tree (auto-generated)"),
    )
    page_type = models.CharField(
        max_length=50,
        choices=PageTypes.choices,
        default=PageTypes.CONTENT,
        help_text=_("Type of page"),
    )
    body = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Page content as list of block references or inline blocks"),
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("SEO metadata, social image, custom fields"),
    )
    is_published = models.BooleanField(
        default=False,
        help_text=_("Whether this page is publicly visible"),
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the page was first published"),
    )

    class Meta:
        abstract = True
        ordering = ["path"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug if not set
        if not self.slug:
            self.slug = slugify(self.title)

        # Build materialized path
        self._build_path()

        super().save(*args, **kwargs)

    def _build_path(self):
        """Build the materialized path from parent hierarchy."""
        if hasattr(self, "parent") and self.parent:
            self.path = f"{self.parent.path.rstrip('/')}/{self.slug}/"
            self.depth = self.parent.depth + 1
        else:
            self.path = f"/{self.slug}/" if self.slug else "/"
            self.depth = 0

    def publish(self):
        """Publish this page."""
        self.is_published = True
        if not self.published_at:
            self.published_at = timezone.now()
        self.save()

    def unpublish(self):
        """Unpublish this page."""
        self.is_published = False
        self.save()

    def get_url(self):
        """Get the full URL for this page."""
        if hasattr(self, "site"):
            return f"https://{self.site.domain}{self.path}"
        return self.path

    def get_children(self):
        """Get child pages (must be implemented by concrete model)."""
        raise NotImplementedError("Concrete model must implement get_children()")

    def get_siblings(self):
        """Get sibling pages (must be implemented by concrete model)."""
        raise NotImplementedError("Concrete model must implement get_siblings()")


class BaseBlock(BaseModel):
    """
    Reusable content blocks with JSON-based props.

    Blocks can be referenced by pages or embedded inline.
    Props schema varies by block_type.
    """

    # Note: site ForeignKey must be defined in concrete model

    block_type = models.CharField(
        max_length=50,
        choices=BlockTypes.choices,
        help_text=_("Type of content block"),
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Optional name for reusable blocks"),
    )
    props = models.JSONField(
        default=dict,
        help_text=_("Block properties (content, src, alt, etc.)"),
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.block_type})"
        return f"{self.block_type} block"


class BaseNavItem(BaseModel):
    """
    Navigation items per site.

    Supports hierarchical navigation menus with multiple locations.
    """

    # Note: site, parent, and page ForeignKeys must be defined in concrete model

    menu_location = models.CharField(
        max_length=50,
        default="main",
        help_text=_("Menu location (main, footer, sidebar, etc.)"),
    )
    label = models.CharField(
        max_length=100,
        help_text=_("Display text for this nav item"),
    )
    url = models.CharField(
        max_length=500,
        blank=True,
        help_text=_("External URL (leave blank to use linked page)"),
    )
    # page FK defined in concrete model
    order = models.PositiveIntegerField(
        default=0,
        help_text=_("Sort order within menu"),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this nav item is visible"),
    )
    css_class = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Optional CSS classes"),
    )
    open_in_new_tab = models.BooleanField(
        default=False,
        help_text=_("Open link in new tab"),
    )

    class Meta:
        abstract = True
        ordering = ["order"]

    def __str__(self):
        return self.label

    def get_url(self):
        """Get the URL for this nav item."""
        if self.url:
            return self.url
        if hasattr(self, "page") and self.page:
            return self.page.get_url()
        return "#"


class BaseComponent(BaseModel):
    """
    Pre-configured UI component instances.

    Stores props for React/frontend components that can be
    embedded in pages or used site-wide (e.g., hero sections).
    """

    # Note: site ForeignKey must be defined in concrete model

    name = models.CharField(
        max_length=100,
        help_text=_("Component instance name"),
    )
    component_type = models.CharField(
        max_length=100,
        help_text=_("Component type (hero, cta, feature-grid, etc.)"),
    )
    props = models.JSONField(
        default=dict,
        help_text=_("Component props as JSON"),
    )
    is_global = models.BooleanField(
        default=False,
        help_text=_("Available site-wide (header, footer, etc.)"),
    )

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.component_type})"
