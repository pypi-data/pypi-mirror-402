"""
Template tags for LightWave islands.

Provides tags for building island props from Django context.

Security Notes:
- JSON data is passed to islands via data-* attributes
- Django's auto-escaping handles XSS protection for data-* attributes
- For extra security, use the json_script pattern (recommended for large data)
- Never use mark_safe() on user-provided data

Two patterns for passing JSON to islands:

1. data-* attributes (current, simple):
   {% island_json company_info as json %}
   <div id="header-root" data-company-info="{{ json }}">

2. json_script pattern (recommended for large data):
   {% island_script company_info "company-info-data" %}
   <div id="header-root" data-company-id="company-info-data">

   JavaScript reads: parseJsonScript("company-info-data", {})
"""

import json
from typing import Any

from django import template
from django.middleware.csrf import get_token
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def auth_form_props(context: dict[str, Any], page_type: str = "") -> str:
    """
    Build auth form props JSON from Django context.

    Usage in template:
        {% load island_tags %}
        {% auth_form_props "signup" as auth_form_props %}
        <div data-auth-props="{{ auth_form_props }}">

    Args:
        page_type: One of "login", "signup", "password_reset", "verification_sent"
                   Used to load content from auth.pages config.

    Extracts from context:
        - form: Django form object (errors, initial data)
        - request: For CSRF token and path
        - email: For verification/reset flows
        - success_message: Flash message after action
        - lightwave_config: For auth page content (headline, subheadline)
    """
    request = context.get("request")
    form = context.get("form")
    config = context.get("lightwave_config", {})

    props: dict[str, Any] = {}

    # Get page-specific content from config
    if page_type:
        auth_pages = config.get("auth", {}).get("pages", {})
        page_content = auth_pages.get(page_type, {})
        if page_content:
            if "headline" in page_content:
                props["headline"] = page_content["headline"]
            if "subheadline" in page_content:
                props["subheadline"] = page_content["subheadline"]

    # CSRF token
    if request:
        props["csrf_token"] = get_token(request)
        props["form_action"] = request.path

    # Form errors
    if form:
        if hasattr(form, "errors") and form.errors:
            # Convert ErrorDict to plain dict of lists
            props["errors"] = {
                field: [str(e) for e in errors] for field, errors in form.errors.items() if field != "__all__"
            }

        # Non-field errors
        if hasattr(form, "non_field_errors"):
            non_field = form.non_field_errors()
            if non_field:
                props["non_field_errors"] = [str(e) for e in non_field]

        # Initial values (for re-populating form after error)
        if hasattr(form, "data") and form.data:
            # Only include safe fields, not passwords
            safe_fields = {"email", "login", "username", "remember"}
            props["initial_values"] = {k: v for k, v in form.data.items() if k in safe_fields and v}

    # Email for verification/reset flows
    if "email" in context:
        props["email"] = context["email"]

    # Success message
    if "success_message" in context:
        props["success_message"] = context["success_message"]

    return json.dumps(props)


@register.simple_tag(takes_context=True)
def island_props(context: dict[str, Any], *args: str) -> str:
    """
    Build generic island props JSON from context variables.

    Usage:
        {% island_props "form" "user" "page" as props %}
        <div data-props="{{ props }}">

    Extracts named context variables and serializes to JSON.
    """
    props: dict[str, Any] = {}

    for var_name in args:
        if var_name in context:
            value = context[var_name]
            # Handle common Django objects
            if hasattr(value, "to_dict"):
                props[var_name] = value.to_dict()
            elif hasattr(value, "__dict__"):
                # Skip complex objects that can't be serialized
                continue
            else:
                props[var_name] = value

    return json.dumps(props)


@register.simple_tag
def island_json(value: Any) -> str:
    """
    Convert a Python value to a JSON string for use in data-* attributes.

    Usage:
        {% island_json company_info as json %}
        <div data-company-info="{{ json }}">

    This is a simple wrapper around json.dumps that's explicit about intent.
    Django's auto-escaping will handle XSS protection.
    """
    if value is None:
        return "{}"
    if isinstance(value, str):
        # If already a JSON string, return as-is
        try:
            json.loads(value)
            return value
        except (json.JSONDecodeError, TypeError):
            pass
    return json.dumps(value)


@register.simple_tag
def island_script(value: Any, element_id: str) -> str:
    """
    Output a JSON value as a <script type="application/json"> element.

    This is the recommended pattern for large JSON data as it avoids
    attribute escaping and is more secure against certain edge cases.

    Usage in Django template:
        {% island_script company_info "company-info-data" %}
        <div id="header-root" data-company-id="company-info-data">

    Usage in JavaScript:
        import { parseJsonScript } from '@lightwave-media/ui';
        const companyInfo = parseJsonScript("company-info-data", {});

    Args:
        value: Python dict/list to serialize
        element_id: ID for the script element (used to retrieve in JS)

    Returns:
        HTML string with script element (marked safe for template output)
    """
    from django.core.serializers.json import DjangoJSONEncoder

    if value is None:
        data = {}
    elif isinstance(value, str):
        # If already a JSON string, parse it first
        try:
            data = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            data = value
    else:
        data = value

    # Escape for safe inclusion in script context
    # Django's json_script pattern escapes <, >, and & to prevent XSS
    json_str = json.dumps(data, cls=DjangoJSONEncoder)

    # Escape characters that could break out of script context
    # This matches Django's _json_script_escapes
    escapes = {
        ord(">"): "\\u003E",
        ord("<"): "\\u003C",
        ord("&"): "\\u0026",
    }
    json_str = json_str.translate(escapes)

    return mark_safe(f'<script type="application/json" id="{element_id}">{json_str}</script>')
