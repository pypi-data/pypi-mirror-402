"""
Navigation helpers for LightWave islands.

This module provides utilities for building navigation structures
that can be used by React island components.
"""

from typing import Any, TypedDict


class NavItem(TypedDict, total=False):
    """A navigation item."""

    label: str
    href: str
    hasMenu: bool


class FooterCategory(TypedDict, total=False):
    """A footer navigation category."""

    label: str
    items: list[NavItem]


class AuthConfig(TypedDict, total=False):
    """Authentication configuration."""

    show_signup: bool
    show_login: bool
    invite_only: bool
    login_url: str
    signup_url: str | None
    logout_url: str
    dashboard_url: str


class BrandConfig(TypedDict, total=False):
    """Brand/company configuration."""

    name: str
    description: str
    email: str


class IslandsConfig(TypedDict, total=False):
    """Islands JavaScript paths configuration."""

    header_js: str
    footer_js: str


class LightwaveConfig(TypedDict, total=False):
    """Complete LIGHTWAVE_CONFIG schema."""

    brand: BrandConfig
    navigation: dict[str, Any]
    auth: AuthConfig
    islands: IslandsConfig


# Default configurations for fallback
DEFAULT_AUTH_CONFIG: AuthConfig = {
    "show_signup": True,
    "show_login": True,
    "invite_only": False,
    "login_url": "/accounts/login/",
    "signup_url": "/accounts/signup/",
    "logout_url": "/accounts/logout/",
    "dashboard_url": "/dashboard/",
}

DEFAULT_BRAND_CONFIG: BrandConfig = {
    "name": "LightWave Media",
    "description": "",
    "email": "",
}
