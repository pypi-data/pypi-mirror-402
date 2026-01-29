"""
Block rendering utilities for LightWave CMS.

Provides functions to render blocks to HTML for use in Django templates.
"""

import logging

import nh3
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

# Default allowed tags for rich text content (paragraphs, captions, etc.)
DEFAULT_RICH_TEXT_TAGS = {
    "a",
    "abbr",
    "b",
    "br",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "p",
    "span",
    "strong",
    "sub",
    "sup",
    "u",
    "ul",
}

# Allowed attributes for rich text
DEFAULT_RICH_TEXT_ATTRIBUTES = {
    "a": {"href", "title", "rel", "target"},
    "abbr": {"title"},
    "span": {"class"},
}

# Extended tags for raw HTML blocks (if allowed by settings)
EXTENDED_HTML_TAGS = DEFAULT_RICH_TEXT_TAGS | {
    "article",
    "aside",
    "blockquote",
    "cite",
    "details",
    "div",
    "figure",
    "figcaption",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "iframe",
    "img",
    "nav",
    "pre",
    "section",
    "summary",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "video",
}

EXTENDED_HTML_ATTRIBUTES = {
    **DEFAULT_RICH_TEXT_ATTRIBUTES,
    "div": {"class", "id"},
    "figure": {"class"},
    "figcaption": {"class"},
    "img": {"src", "alt", "width", "height", "loading", "class"},
    "iframe": {"src", "width", "height", "frameborder", "allowfullscreen", "allow"},
    "video": {"src", "controls", "width", "height", "poster", "preload"},
    "table": {"class"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan", "scope"},
}


def sanitize_rich_text(content: str) -> str:
    """
    Sanitize rich text content allowing only safe inline formatting.

    Args:
        content: HTML string that may contain user-supplied content

    Returns:
        Sanitized HTML string safe for rendering
    """
    if not content:
        return ""
    return nh3.clean(
        content,
        tags=DEFAULT_RICH_TEXT_TAGS,
        attributes=DEFAULT_RICH_TEXT_ATTRIBUTES,
    )


def sanitize_html_block(content: str) -> str:
    """
    Sanitize HTML block content with extended tag allowlist.

    Used for raw HTML blocks where more flexibility is needed but still
    need to prevent XSS attacks (no script, style, event handlers).

    Args:
        content: Raw HTML string

    Returns:
        Sanitized HTML string safe for rendering
    """
    if not content:
        return ""
    return nh3.clean(
        content,
        tags=EXTENDED_HTML_TAGS,
        attributes=EXTENDED_HTML_ATTRIBUTES,
    )


# Default block templates
DEFAULT_BLOCK_TEMPLATES = {
    "paragraph": "cms/blocks/paragraph.html",
    "heading": "cms/blocks/heading.html",
    "image": "cms/blocks/image.html",
    "gallery": "cms/blocks/gallery.html",
    "caption": "cms/blocks/caption.html",
    "quote": "cms/blocks/quote.html",
    "code": "cms/blocks/code.html",
    "html": "cms/blocks/html.html",
    "embed": "cms/blocks/embed.html",
    "divider": "cms/blocks/divider.html",
}


def get_block_templates():
    """Get block templates, allowing override via settings."""
    templates = DEFAULT_BLOCK_TEMPLATES.copy()
    custom = getattr(settings, "LIGHTWAVE_CMS_BLOCK_TEMPLATES", {})
    templates.update(custom)
    return templates


def render_block(block, context=None):
    """
    Render a single block to HTML.

    Args:
        block: Block model instance or dict with block_type and props
        context: Optional template context

    Returns:
        Safe HTML string
    """
    if context is None:
        context = {}

    # Handle both model instances and dicts
    if hasattr(block, "block_type"):
        block_type = block.block_type
        props = block.props
    elif isinstance(block, dict):
        block_type = block.get("block_type", block.get("type", "paragraph"))
        props = block.get("props", block)
    else:
        return ""

    templates = get_block_templates()
    template_name = templates.get(block_type)

    if template_name:
        try:
            return render_to_string(
                template_name,
                {
                    "block": block,
                    "block_type": block_type,
                    "props": props,
                    **context,
                },
            )
        except Exception as e:
            # Log the error for debugging, then fall back to inline rendering
            # Use warning level since template errors shouldn't crash the page
            logger.warning(
                "Failed to render template %s for block type %s: %s",
                template_name,
                block_type,
                str(e),
            )

    # Fallback inline rendering for common block types
    return _render_block_inline(block_type, props)


def _render_block_inline(block_type, props):
    """Inline rendering fallback when templates aren't available."""
    if block_type == "paragraph":
        content = props.get("content", "")
        # Sanitize rich text content to prevent XSS
        safe_content = sanitize_rich_text(content)
        return format_html("<p>{}</p>", mark_safe(safe_content))

    elif block_type == "heading":
        content = props.get("content", "")
        level = props.get("level", 2)
        # Validate level is an integer and clamp to h1-h6
        try:
            level = max(1, min(6, int(level)))
        except (ValueError, TypeError):
            level = 2
        return format_html("<h{level}>{content}</h{level}>", level=level, content=escape(content))

    elif block_type == "image":
        src = props.get("src", "")
        alt = props.get("alt", "")
        width = props.get("width", "")
        height = props.get("height", "")
        attrs = f'src="{escape(src)}" alt="{escape(alt)}"'
        if width:
            attrs += f' width="{escape(str(width))}"'
        if height:
            attrs += f' height="{escape(str(height))}"'
        return mark_safe(f"<figure><img {attrs}></figure>")

    elif block_type == "caption":
        text = props.get("text", props.get("content", ""))
        # Sanitize caption text to prevent XSS
        safe_text = sanitize_rich_text(text)
        return format_html("<figcaption>{}</figcaption>", mark_safe(safe_text))

    elif block_type == "quote":
        content = props.get("content", "")
        author = props.get("author", "")
        html = f"<blockquote><p>{escape(content)}</p>"
        if author:
            html += f"<cite>{escape(author)}</cite>"
        html += "</blockquote>"
        return mark_safe(html)

    elif block_type == "code":
        content = props.get("content", "")
        language = props.get("language", "")
        lang_class = f' class="language-{escape(language)}"' if language else ""
        return mark_safe(f"<pre><code{lang_class}>{escape(content)}</code></pre>")

    elif block_type == "html":
        # Raw HTML - sanitize to allow safe HTML tags but prevent XSS
        content = props.get("content", "")
        safe_content = sanitize_html_block(content)
        return mark_safe(safe_content)

    elif block_type == "divider":
        return mark_safe("<hr>")

    elif block_type == "gallery":
        images = props.get("images", [])
        html = '<div class="gallery">'
        for img in images:
            src = img.get("src", "")
            alt = img.get("alt", "")
            caption = img.get("caption", "")
            html += f'<figure><img src="{escape(src)}" alt="{escape(alt)}">'
            if caption:
                html += f"<figcaption>{escape(caption)}</figcaption>"
            html += "</figure>"
        html += "</div>"
        return mark_safe(html)

    elif block_type == "embed":
        url = props.get("url", "")
        html = props.get("html", "")
        if html:
            # Sanitize embed HTML to allow iframes but prevent XSS
            safe_html = sanitize_html_block(html)
            return mark_safe(f'<div class="embed">{safe_html}</div>')
        elif url:
            return mark_safe(f'<div class="embed"><a href="{escape(url)}">{escape(url)}</a></div>')
        return ""

    # Unknown block type
    return format_html(
        '<div class="block block-{type}">{content}</div>',
        type=escape(block_type),
        content=escape(str(props)),
    )


def render_blocks(blocks, context=None):
    """
    Render a list of blocks to HTML.

    Args:
        blocks: List of Block model instances or dicts
        context: Optional template context

    Returns:
        Safe HTML string
    """
    if not blocks:
        return ""

    rendered = []
    for block in blocks:
        rendered.append(render_block(block, context))

    return mark_safe("".join(rendered))


def render_page_body(page, context=None):
    """
    Render a page's body content.

    The body field can contain:
    - List of block dicts (inline blocks)
    - List of block IDs (references to Block model)

    Args:
        page: Page model instance
        context: Optional template context

    Returns:
        Safe HTML string
    """
    if not page.body:
        return ""

    # If body contains dicts, render inline
    if isinstance(page.body, list) and page.body:
        first = page.body[0]
        if isinstance(first, dict):
            return render_blocks(page.body, context)

        # Otherwise assume block IDs - this requires the Block model
        # which should be handled by project-specific code
        pass

    return ""
