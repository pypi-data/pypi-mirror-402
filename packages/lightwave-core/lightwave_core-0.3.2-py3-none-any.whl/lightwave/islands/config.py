"""
YAML configuration loader for LightWave domains.

This module provides utilities to load lightwave-config.yaml files,
which configure brand, navigation, auth, and island settings for domains.

Similar to pegasus-config.yaml but focused on runtime configuration
rather than code generation.

Usage in settings.py:
    from lightwave.islands.config import load_lightwave_config

    LIGHTWAVE_CONFIG = load_lightwave_config(BASE_DIR / "lightwave-config.yaml")
"""

import os
from pathlib import Path
from typing import Any, TypedDict

import yaml


class BrandConfig(TypedDict, total=False):
    """Brand/company configuration."""

    name: str
    description: str
    email: str
    logo_url: str
    logo_minimal_url: str
    favicon_url: str


class NavItem(TypedDict, total=False):
    """Navigation item."""

    label: str
    href: str
    items: list["NavItem"]


class NavigationConfig(TypedDict, total=False):
    """Navigation configuration."""

    header: list[NavItem]
    footer: list[NavItem]


class AuthConfig(TypedDict, total=False):
    """Authentication configuration."""

    show_signup: bool
    invite_only: bool
    login_url: str
    signup_url: str
    logout_url: str
    dashboard_url: str


class IslandsConfig(TypedDict, total=False):
    """React islands configuration."""

    header_js: str
    footer_js: str
    toast_js: str


class FeaturesConfig(TypedDict, total=False):
    """Feature flags."""

    use_teams: bool
    use_chat: bool
    use_subscriptions: bool
    use_cms: bool


class LightwaveConfig(TypedDict, total=False):
    """Complete lightwave-config.yaml schema."""

    brand: BrandConfig
    navigation: NavigationConfig
    auth: AuthConfig
    islands: IslandsConfig
    features: FeaturesConfig


# Default configuration values
DEFAULTS: LightwaveConfig = {
    "brand": {
        "name": "LightWave",
        "description": "",
        "email": "",
    },
    "navigation": {
        "header": [],
        "footer": [],
    },
    "auth": {
        "show_signup": True,
        "invite_only": False,
        "login_url": "/accounts/login/",
        "signup_url": "/accounts/signup/",
        "logout_url": "/accounts/logout/",
        "dashboard_url": "/app/",
    },
    "islands": {
        "header_js": "assets/javascript/islands/header.tsx",
        "footer_js": "assets/javascript/islands/footer.tsx",
    },
    "features": {
        "use_teams": False,
        "use_chat": False,
        "use_subscriptions": False,
        "use_cms": False,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_lightwave_config(
    config_path: str | Path | None = None,
    defaults: LightwaveConfig | None = None,
) -> LightwaveConfig:
    """
    Load lightwave-config.yaml and merge with defaults.

    Args:
        config_path: Path to lightwave-config.yaml file.
                    If None, looks for LIGHTWAVE_CONFIG_PATH env var,
                    then falls back to ./lightwave-config.yaml
        defaults: Override default values. If None, uses DEFAULTS.

    Returns:
        Merged configuration dictionary.

    Example:
        # In settings.py
        from lightwave.islands.config import load_lightwave_config

        LIGHTWAVE_CONFIG = load_lightwave_config(BASE_DIR / "lightwave-config.yaml")
    """
    base_config = defaults if defaults is not None else DEFAULTS.copy()

    # Resolve config path
    if config_path is None:
        config_path = os.environ.get("LIGHTWAVE_CONFIG_PATH", "lightwave-config.yaml")

    path = Path(config_path)

    # If path doesn't exist, return defaults
    if not path.exists():
        return base_config

    # Load YAML
    with path.open("r") as f:
        yaml_config = yaml.safe_load(f) or {}

    # Deep merge with defaults
    return _deep_merge(base_config, yaml_config)


def get_config_template() -> str:
    """
    Get a template lightwave-config.yaml with documentation.

    Returns:
        YAML string template for new domains.
    """
    return """# lightwave-config.yaml
# Configuration for LightWave domain
# Docs: https://github.com/lightwave-media/lightwave-core

# =============================================================================
# BRAND
# =============================================================================
# Company/brand information displayed in headers, footers, and meta tags.

brand:
  name: "Your Brand"
  description: "Your brand description for meta tags"
  email: "hello@yourdomain.com"

  # Logo URLs - use CDN paths for production
  logo_url: "https://cdn.lightwave-media.ltd/brands/yourbrand/logo.png"
  logo_minimal_url: "https://cdn.lightwave-media.ltd/brands/yourbrand/logomark.png"
  favicon_url: "https://cdn.lightwave-media.ltd/brands/yourbrand/favicon.ico"

# =============================================================================
# NAVIGATION
# =============================================================================
# Header and footer navigation items.

navigation:
  # Header navigation (visible in main nav bar)
  header:
    - label: "Features"
      href: "/features/"
    - label: "Pricing"
      href: "/pricing/"
    - label: "About"
      href: "/about/"

  # Footer navigation (grouped by category)
  footer:
    - label: "Product"
      items:
        - label: "Overview"
          href: "/"
        - label: "Features"
          href: "/features/"
        - label: "Pricing"
          href: "/pricing/"

    - label: "Company"
      items:
        - label: "About"
          href: "/about/"
        - label: "Contact"
          href: "/contact/"

    - label: "Legal"
      items:
        - label: "Privacy"
          href: "/privacy/"
        - label: "Terms"
          href: "/terms/"

# =============================================================================
# AUTHENTICATION
# =============================================================================
# Auth behavior and URLs.

auth:
  show_signup: true         # Show signup button in header
  invite_only: false        # Require invite code for signup
  login_url: "/accounts/login/"
  signup_url: "/accounts/signup/"
  logout_url: "/accounts/logout/"
  dashboard_url: "/app/"    # Where to redirect after login

# =============================================================================
# ISLANDS
# =============================================================================
# React island JavaScript entry points.
# These are relative to the assets/ directory.

islands:
  header_js: "assets/javascript/islands/header.tsx"
  footer_js: "assets/javascript/islands/footer.tsx"

# =============================================================================
# FEATURES
# =============================================================================
# Feature flags for enabling/disabling functionality.

features:
  use_teams: false          # Multi-tenant team support
  use_chat: false           # AI chat functionality
  use_subscriptions: false  # Stripe subscription billing
  use_cms: false            # Headless CMS integration
"""
