"""
Template tags for LightWave CMS.

Usage in templates:
    {% load cms_tags %}

    {# Render page body #}
    {% render_page_body page %}

    {# Render a list of blocks #}
    {% render_blocks blocks %}

    {# Render a single block #}
    {% render_block block %}

    {# Get navigation for current site #}
    {% cms_nav "main" as main_nav %}
    {% for item in main_nav %}
        <a href="{{ item.url }}">{{ item.label }}</a>
    {% endfor %}
"""

from django import template
from django.utils.safestring import mark_safe

from ..renderers import render_block as _render_block
from ..renderers import render_blocks as _render_blocks
from ..renderers import render_page_body as _render_page_body

register = template.Library()


@register.simple_tag
def render_block(block, **kwargs):
    """
    Render a single block to HTML.

    Usage:
        {% render_block block %}
        {% render_block block extra_class="featured" %}
    """
    return mark_safe(_render_block(block, context=kwargs))


@register.simple_tag
def render_blocks(blocks, **kwargs):
    """
    Render a list of blocks to HTML.

    Usage:
        {% render_blocks page.body %}
        {% render_blocks blocks wrapper_class="content" %}
    """
    return mark_safe(_render_blocks(blocks, context=kwargs))


@register.simple_tag
def render_page_body(page, **kwargs):
    """
    Render a page's body content.

    Usage:
        {% render_page_body page %}
    """
    return mark_safe(_render_page_body(page, context=kwargs))


@register.simple_tag(takes_context=True)
def cms_nav(context, location="main", site=None):
    """
    Get navigation items for a menu location.

    Usage:
        {% cms_nav "main" as main_nav %}
        {% cms_nav "footer" site=other_site as footer_nav %}

    Args:
        location: Menu location (default: "main")
        site: Site instance (default: from request)

    Returns:
        QuerySet of NavItem instances
    """
    request = context.get("request")

    # Get site from context or request
    if site is None:
        site = context.get("site")
        if site is None and request:
            site = getattr(request, "site", None)

    if site is None:
        return []

    try:
        return (
            site.nav_items.filter(
                menu_location=location,
                is_active=True,
                parent__isnull=True,
            )
            .order_by("order")
            .select_related("page")
        )
    except AttributeError:
        # Site doesn't have nav_items relation
        return []


@register.simple_tag(takes_context=True)
def cms_component(context, name, site=None):
    """
    Get a component by name.

    Usage:
        {% cms_component "hero-homepage" as hero %}
        {{ hero.props.headline }}

    Args:
        name: Component name
        site: Site instance (default: from request)

    Returns:
        Component instance or None
    """
    request = context.get("request")

    if site is None:
        site = context.get("site")
        if site is None and request:
            site = getattr(request, "site", None)

    if site is None:
        return None

    try:
        return site.components.filter(name=name).first()
    except AttributeError:
        return None


@register.inclusion_tag("cms/components/nav_item.html")
def render_nav_item(item, depth=0):
    """
    Render a navigation item with children.

    Usage:
        {% render_nav_item item %}
    """
    return {
        "item": item,
        "depth": depth,
        "children": item.children.filter(is_active=True).order_by("order") if hasattr(item, "children") else [],
    }


@register.filter
def block_class(block):
    """
    Get CSS class for a block.

    Usage:
        <div class="block {{ block|block_class }}">
    """
    if hasattr(block, "block_type"):
        return f"block-{block.block_type}"
    elif isinstance(block, dict):
        block_type = block.get("block_type", block.get("type", "unknown"))
        return f"block-{block_type}"
    return "block-unknown"
