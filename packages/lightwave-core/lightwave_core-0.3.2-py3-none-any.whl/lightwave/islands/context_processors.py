"""
Shared context processors for LightWave islands.

These context processors inject navigation, auth, and brand data
into Django templates for use by React island components.

Configuration sources (in priority order):
1. Site.settings (database) - recommended for production
2. settings.LIGHTWAVE_CONFIG (YAML file or dict) - legacy/development fallback

The database approach enables the stampable multi-domain architecture:
- Same codebase serves multiple domains
- Each domain has a Site record with its own settings
- Content changes don't require code deploys

Migration path:
1. Add SiteMiddleware to MIDDLEWARE (attaches request.site)
2. Run migrate_yaml_to_db management command
3. Update lightwave-config.yaml to just: domain: "your-domain.com"
4. Edit site settings in Django admin or via Notion sync

Legacy mode (YAML-only):
    from lightwave.islands.config import load_lightwave_config
    LIGHTWAVE_CONFIG = load_lightwave_config(BASE_DIR / "lightwave-config.yaml")

Database mode (recommended):
    # lightwave-config.yaml
    domain: "lightwave-media.site"

    # Site.settings JSON in database contains all config
"""

import copy
import json
from typing import Any

from django.conf import settings
from django.http import HttpRequest

# Brand color mapping for multi-tenant theming
# Maps tenant slugs to their brand colors for public/marketing sites
TENANT_BRAND_COLORS: dict[str, str] = {
    "cineos": "blue",
    "joelschaeffer": "blue",
    "photographyos": "blue",
    "createos": "blue-dark",
    "lightwave-media": "indigo",  # Special: corporate site
}

# Admin/app domains always use violet
ADMIN_BRAND_COLOR = "violet"

# Default fallback
DEFAULT_BRAND_COLOR = "blue"

# CDN domain for auto-populating logo URLs
CDN_DOMAIN = "cdn.lightwave-media.ltd"


def _extract_tenant_slug(domain: str) -> str:
    """
    Extract tenant slug from domain name for CDN logo paths.

    Examples:
        cineos.io -> cineos
        local.cineos.io -> cineos
        app.lightwave-media.site -> lightwave-media
        admin.local.lightwave-media.ltd -> lightwave-media
    """
    if not domain:
        return "lightwave"

    parts = domain.split(".")

    # Skip environment/subdomain prefixes
    prefixes_to_skip = {"local", "staging", "app", "www", "admin", "api", "ws", "cdn"}
    while parts and parts[0] in prefixes_to_skip:
        parts = parts[1:]

    if not parts:
        return "lightwave"

    # Return the first meaningful part
    slug = parts[0]

    # Handle special cases
    if slug == "lightwave-media":
        return "lightwave-media"

    return slug


def _get_brand_with_auto_logos(request: HttpRequest, brand: dict[str, Any]) -> dict[str, Any]:
    """
    Auto-populate logo URLs from CDN if not explicitly set in brand config.

    CDN path convention:
        /brands/{tenant_slug}/logo.png        - Full logo
        /brands/{tenant_slug}/logomark.png    - Icon/minimal logo
        /brands/{tenant_slug}/favicon.ico     - Favicon

    Priority:
        1. Explicit URLs in brand config (Site.settings.brand)
        2. Auto-generated from CDN + tenant slug
    """
    brand = copy.deepcopy(brand)  # Don't modify original

    # Get tenant slug from request
    site = getattr(request, "site", None)
    domain = site.domain if site else request.get_host().split(":")[0]
    tenant_slug = _extract_tenant_slug(domain)

    cdn_base = f"https://{CDN_DOMAIN}/brands/{tenant_slug}"

    # Auto-populate logo_url if not set
    if not brand.get("logo_url"):
        brand["logo_url"] = f"{cdn_base}/logo.png"

    # Auto-populate logo_minimal_url if not set
    if not brand.get("logo_minimal_url"):
        brand["logo_minimal_url"] = f"{cdn_base}/logomark.png"

    # Auto-populate favicon if not set
    favicon = brand.setdefault("favicon", {})
    if not favicon.get("ico"):
        favicon["ico"] = f"{cdn_base}/favicon.ico"
    if not favicon.get("svg"):
        favicon["svg"] = f"{cdn_base}/favicon.svg"

    # Auto-populate assets (for auth islands)
    assets = brand.setdefault("assets", {})
    if not assets.get("logo_header"):
        assets["logo_header"] = brand["logo_url"]
    if not assets.get("logo_minimal"):
        assets["logo_minimal"] = brand["logo_minimal_url"]

    return brand


def _get_brand_theme(request: HttpRequest, config: dict[str, Any]) -> str:
    """
    Determine the brand theme color based on domain and user preference.

    Priority order:
    1. User preference (authenticated users with stored preference)
    2. Domain type (app.* domains always use violet)
    3. Tenant-specific default (from TENANT_BRAND_COLORS)
    4. Config override (theme.brand_color in site settings)
    5. Default (blue)

    Returns one of: 'blue', 'blue-dark', 'indigo', 'violet'
    """
    # Check for user preference (authenticated users)
    user = request.user
    if user.is_authenticated:
        # Try to get user's brand preference from profile
        profile = getattr(user, "profile", None)
        if profile:
            user_brand = getattr(profile, "brand_color", None)
            if user_brand and user_brand in ("blue", "blue-dark", "indigo", "violet"):
                return user_brand

    # Check domain type - app.* domains use admin theme
    host = request.get_host().split(":")[0]  # Remove port if present
    if host.startswith("app.") or host.endswith(".ltd"):
        return ADMIN_BRAND_COLOR

    # Check config override
    theme = config.get("theme", {})
    if "brand_color" in theme:
        return theme["brand_color"]

    # Get tenant slug and map to brand color
    site = getattr(request, "site", None)
    if site:
        # Try site.tenant_slug first, then domain-based detection
        tenant_slug = getattr(site, "tenant_slug", None)
        if tenant_slug and tenant_slug in TENANT_BRAND_COLORS:
            return TENANT_BRAND_COLORS[tenant_slug]

        # Fallback: detect from domain
        domain = getattr(site, "domain", host)
        for tenant, color in TENANT_BRAND_COLORS.items():
            if tenant in domain:
                return color

    # Final fallback: detect from host
    for tenant, color in TENANT_BRAND_COLORS.items():
        if tenant in host:
            return color

    return DEFAULT_BRAND_COLOR


def _get_user_avatar_url(user: Any) -> str:
    """
    Get user's avatar URL from social auth or uploaded avatar.

    Priority:
    1. User's uploaded avatar (if exists)
    2. Google social auth picture
    3. Empty string (frontend should show initials)
    """
    # Check for uploaded avatar
    if hasattr(user, "avatar") and user.avatar:
        try:
            return user.avatar.url
        except (ValueError, AttributeError):
            pass

    # Check for Google social auth picture
    try:
        from allauth.socialaccount.models import SocialAccount

        google_account = SocialAccount.objects.filter(user=user, provider="google").first()
        if google_account and google_account.extra_data:
            return google_account.extra_data.get("picture", "")
    except (ImportError, Exception):
        pass

    return ""


def _get_user_initials(user: Any) -> str:
    """Get user's initials from their name or email."""
    # Try get_initials method first
    if hasattr(user, "get_initials"):
        return user.get_initials()

    # Derive from name
    name = getattr(user, "get_full_name", lambda: "")() or getattr(user, "email", "")
    if not name:
        return ""

    parts = name.split()
    if "@" in name and len(parts) == 1:
        # Email only - use first two chars of local part
        local_part = name.split("@")[0]
        return local_part[:2].upper()

    return "".join(p[0].upper() for p in parts[:2])


def _get_auth_state(request: HttpRequest) -> dict[str, Any]:
    """
    Get current user's authentication state for frontend display.

    Returns camelCase keys for JSON serialization to React components:
    - isAuthenticated: boolean
    - user: { name, email, avatarUrl, initials }

    SECURITY NOTE: This data is passed to the frontend via data-* attributes
    and is used ONLY for UI rendering (show login vs avatar). It must NOT
    contain sensitive data or be used for authorization decisions.

    All authorization must happen server-side via @login_required, DRF
    permissions, or Django's permission system.
    """
    user = request.user
    if user.is_authenticated:
        # Get display name
        name = ""
        if hasattr(user, "get_display_name"):
            name = user.get_display_name()
        else:
            name = getattr(user, "get_full_name", lambda: "")() or getattr(user, "email", "")

        return {
            "isAuthenticated": True,
            "user": {
                # NOTE: user.id intentionally omitted to prevent enumeration attacks
                "name": name,
                "email": getattr(user, "email", ""),
                "avatarUrl": _get_user_avatar_url(user),
                "initials": _get_user_initials(user),
                "hasVerifiedEmail": getattr(user, "has_verified_email", False),
            },
        }
    return {
        "isAuthenticated": False,
        "user": None,
    }


def _get_auth_ui_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Build enhanced auth UI configuration from site config.

    Supports three auth modes:
    - "private": Login only, no signup, invite-only (admin sites)
    - "ecommerce": Public signup, guest checkout, cart
    - "subscription": Public signup, plans, roles, access flags

    Returns config used by header and auth islands for UI decisions.
    """
    auth = config.get("auth", {})
    brand = config.get("brand", {})

    # Determine mode from config
    mode = auth.get("mode", "subscription")  # Default to subscription for SaaS

    # Legacy compatibility: infer mode from old flags
    if "mode" not in auth:
        if auth.get("invite_only", False) and not auth.get("show_signup", True):
            mode = "private"
        elif config.get("features", {}).get("use_ecommerce", False):
            mode = "ecommerce"

    # Get UI overrides or use mode-based defaults
    ui = auth.get("ui", {})

    # Mode-based defaults
    mode_defaults = {
        "private": {
            "show_login_button": True,
            "show_signup_button": False,
            "admin_badge": True,
            "login_heading": "Welcome back",
            "login_subheading": f"Sign in to {brand.get('name', 'admin')}",
        },
        "ecommerce": {
            "show_login_button": True,
            "show_signup_button": True,
            "admin_badge": False,
            "login_heading": "Sign in to your account",
            "login_subheading": "Access your orders and wishlist",
            "signup_heading": "Create an account",
            "signup_subheading": "Track orders and save your favorites",
        },
        "subscription": {
            "show_login_button": True,
            "show_signup_button": True,
            "admin_badge": False,
            "login_heading": "Welcome back",
            "login_subheading": f"Sign in to {brand.get('name', 'your account')}",
            "signup_heading": "Get started",
            "signup_subheading": "Create your free account",
        },
    }

    defaults = mode_defaults.get(mode, mode_defaults["subscription"])

    # Social providers (Google on everything by default)
    social_providers = auth.get("social_providers", ["google"])
    if isinstance(social_providers, list) and social_providers:
        # Convert simple list to full config if needed
        if isinstance(social_providers[0], str):
            social_providers = [
                {"provider": p, "enabled": True, "button_text": f"Continue with {p.title()}"} for p in social_providers
            ]

    # URLs with defaults
    urls = auth.get("urls", {})
    default_urls = {
        "login": auth.get("login_url", "/accounts/login/"),
        "signup": auth.get("signup_url", "/accounts/signup/"),
        "logout": auth.get("logout_url", "/accounts/logout/"),
        "password_reset": auth.get("password_reset_url", "/accounts/password/reset/"),
        "after_login": auth.get("dashboard_url", "/app/"),
        "after_signup": auth.get("dashboard_url", "/app/"),
        "after_logout": "/",
    }
    urls = {**default_urls, **urls}

    # Build merged UI config
    merged_ui = {**defaults, **ui}

    return {
        "mode": mode,
        "ui": merged_ui,
        "social_providers": social_providers,
        "urls": urls,
        # Mode-specific settings
        "subscription": auth.get("subscription", {}),
        "ecommerce": auth.get("ecommerce", {}),
        # Legal links
        "show_terms_link": ui.get("show_terms_link", True),
        "show_privacy_link": ui.get("show_privacy_link", True),
        "terms_url": config.get("legal", {}).get("terms_of_service_url", "/terms/"),
        "privacy_url": config.get("legal", {}).get("privacy_policy_url", "/privacy/"),
        # =================================================================
        # Flat camelCase keys for React component compatibility
        # These mirror AuthConfig interface in lightwave-ui
        # =================================================================
        "showSignup": merged_ui.get("show_signup_button", True),
        "showLogin": merged_ui.get("show_login_button", True),
        "loginUrl": urls.get("login", "/accounts/login/"),
        "signupUrl": urls.get("signup", "/accounts/signup/"),
        "logoutUrl": urls.get("logout", "/accounts/logout/"),
        "profileUrl": auth.get("profile_url", "/app/profile/"),
        "settingsUrl": auth.get("settings_url", "/app/settings/"),
        "dashboardUrl": urls.get("after_login", "/app/"),
    }


def _get_cart_state(request: HttpRequest) -> dict[str, Any]:
    """
    Get cart state for e-commerce sites.

    Returns cart data for header cart icon display.
    Only populated for sites with ecommerce mode.
    """
    # Check if ecommerce is enabled
    config = _get_site_config(request)
    auth_mode = config.get("auth", {}).get("mode", "")

    if auth_mode != "ecommerce":
        return {"enabled": False}

    # Try to get cart from session or user
    try:
        # Import cart model - adjust path based on your ecommerce app
        from apps.store.cart import get_cart

        cart = get_cart(request)
        return {
            "enabled": True,
            "item_count": cart.item_count if cart else 0,
            "total": str(cart.total) if cart else "0.00",
            "currency": config.get("i18n", {}).get("currency", "USD"),
        }
    except (ImportError, Exception):
        return {"enabled": True, "item_count": 0, "total": "0.00", "currency": "USD"}


def _get_team_state(request: HttpRequest) -> dict[str, Any]:
    """
    Get current team/workspace context for multi-tenant apps.

    Returns team info for header team switcher and sidebar.
    Only populated for sites with teams enabled.
    """
    config = _get_site_config(request)
    if not config.get("features", {}).get("use_teams", False):
        return {"enabled": False}

    user = request.user
    if not user.is_authenticated:
        return {"enabled": True, "current_team": None, "teams": []}

    try:
        # Try to get team from request (set by team middleware)
        current_team = getattr(request, "team", None)

        # Get user's teams
        if hasattr(user, "teams"):
            teams = [
                {
                    "id": str(team.id),
                    "name": team.name,
                    "slug": getattr(team, "slug", ""),
                    "logo_url": getattr(team, "logo_url", ""),
                    "is_current": current_team and team.id == current_team.id,
                }
                for team in user.teams.all()[:10]  # Limit to 10 teams
            ]
        else:
            teams = []

        return {
            "enabled": True,
            "current_team": {
                "id": str(current_team.id),
                "name": current_team.name,
                "slug": getattr(current_team, "slug", ""),
                "logo_url": getattr(current_team, "logo_url", ""),
            }
            if current_team
            else None,
            "teams": teams,
        }
    except Exception:
        return {"enabled": True, "current_team": None, "teams": []}


def _get_subscription_state(request: HttpRequest) -> dict[str, Any]:
    """
    Get subscription/plan state for SaaS sites.

    Returns subscription info for plan badges, upgrade prompts, and feature gating.
    Merges subscription-level features (from ProductMetadata) with tenant-level
    features (from Tenant.features JSONField).

    Only populated for sites with subscriptions enabled.
    """
    config = _get_site_config(request)
    if not config.get("features", {}).get("use_subscriptions", False):
        return {"enabled": False, "features": []}

    user = request.user
    if not user.is_authenticated:
        return {"enabled": True, "plan": None, "status": "none", "features": []}

    try:
        from django.db import connection

        # Get tenant-level features
        tenant = getattr(connection, "tenant", None)
        tenant_features = []
        if tenant and hasattr(tenant, "features") and tenant.features:
            # Tenant.features is a JSONField with feature flags as keys
            tenant_features = [k for k, v in tenant.features.items() if v is True]

        # Try to get subscription from team (SubscriptionModelBase pattern)
        team = getattr(request, "team", None)
        subscription = None

        if team and hasattr(team, "subscription"):
            subscription = team.subscription
        elif hasattr(user, "subscription"):
            subscription = getattr(user, "subscription", None)

        if subscription:
            # Get plan-level features from ProductMetadata
            plan_features = []
            try:
                from apps.subscriptions.metadata import get_product_with_metadata

                product = subscription.plan.product
                product_with_meta = get_product_with_metadata(product)
                plan_features = list(product_with_meta.metadata.features)
            except Exception:
                pass

            # Merge features (dedupe)
            all_features = list(set(plan_features + tenant_features))

            return {
                "enabled": True,
                "plan": {
                    "name": subscription.plan.product.name if subscription.plan else "",
                    "id": subscription.plan.product.id if subscription.plan else "",
                    "slug": subscription.plan.product.metadata.get("slug", "") if subscription.plan else "",
                },
                "status": subscription.status,
                "trialEndsAt": subscription.trial_end.isoformat() if subscription.trial_end else None,
                "currentPeriodEndsAt": (
                    subscription.current_period_end.isoformat() if subscription.current_period_end else None
                ),
                "features": all_features,
            }

        # No subscription, but may have tenant-level features
        return {"enabled": True, "plan": None, "status": "none", "features": tenant_features}
    except Exception:
        return {"enabled": True, "plan": None, "status": "none", "features": []}


def _get_notification_state(request: HttpRequest) -> dict[str, Any]:
    """
    Get notification state for the notification bell icon.

    Returns unread count for header notification indicator.
    """
    user = request.user
    if not user.is_authenticated:
        return {"enabled": False}

    try:
        # Try to get unread notification count
        if hasattr(user, "notifications"):
            unread_count = user.notifications.filter(read=False).count()
        else:
            unread_count = 0

        return {
            "enabled": True,
            "unread_count": min(unread_count, 99),  # Cap at 99 for display
            "has_unread": unread_count > 0,
        }
    except Exception:
        return {"enabled": True, "unread_count": 0, "has_unread": False}


def _get_active_nav_path(request: HttpRequest) -> str:
    """
    Get the current path for active navigation highlighting.

    Returns the current URL path for the frontend to match against nav items.
    """
    return request.path


def _get_featured_posts(request: HttpRequest, page_type: str = "blog", limit: int = 3) -> list[dict[str, Any]]:
    """
    Get featured posts from CMS for injection into navigation menus.

    Returns list of dicts with: title, subtitle/excerpt, imageUrl, href
    """
    site = getattr(request, "site", None)
    if not site:
        return []

    try:
        # Import the Page model from the domain's content app
        from apps.content.models import Page

        posts = Page.get_featured_by_type(site, page_type, limit)
        return [
            {
                "title": post.title,
                "subtitle": post.intro or "",
                "imageUrl": post.get_social_image_url(),
                "href": post.path,
            }
            for post in posts
        ]
    except (ImportError, AttributeError):
        # CMS not available or not set up
        return []


def _enrich_nav_with_cms(request: HttpRequest, nav_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Enrich navigation items with CMS data.

    For nav items with menu.variant == "featured-posts", injects featuredPosts from CMS.
    Deep copies the nav items to avoid mutating the original config.
    """
    # Deep copy to avoid mutating the original config
    enriched = copy.deepcopy(nav_items)

    for item in enriched:
        menu = item.get("menu")
        if not menu:
            continue

        variant = menu.get("variant", "")

        # Inject featured posts for featured-posts variant
        if variant == "featured-posts":
            # Only inject if not already set in YAML
            if "featuredPosts" not in menu or not menu["featuredPosts"]:
                # Determine page type from menu config or default to "blog"
                page_type = menu.get("pageType", "blog")
                limit = menu.get("postsLimit", 3)
                menu["featuredPosts"] = _get_featured_posts(request, page_type, limit)

    return enriched


def _get_seo_defaults() -> dict[str, Any]:
    """
    Default SEO settings to ensure templates never fail on missing keys.

    These are sensible defaults that prevent VariableDoesNotExist errors
    while still allowing CMS to override any value.
    """
    return {
        "default_title": "",
        "default_description": "",
        "default_keywords": [],
        "title_suffix": "",
        "og_type": "website",
        "og_default_image": "",
        "og_site_name": "",
        "twitter_card": "summary_large_image",
        "twitter_site": "",
        "structured_data": {
            "description": "",
        },
    }


def _get_site_config(request: HttpRequest) -> dict[str, Any]:
    """
    Get site configuration from database or YAML fallback.

    Priority order:
    1. request.site.settings (database) - if Site has settings populated
    2. settings.LIGHTWAVE_CONFIG (YAML file or dict) - legacy fallback

    This allows gradual migration from YAML to database.
    Always merges with SEO defaults to prevent template errors.
    """
    # Try database first (via SiteMiddleware)
    site = getattr(request, "site", None)
    if site and hasattr(site, "settings") and site.settings:
        config = site.settings
    else:
        # Fall back to YAML config
        config = getattr(settings, "LIGHTWAVE_CONFIG", {})

    # Ensure SEO defaults are always present (deep merge)
    seo_defaults = _get_seo_defaults()
    config_seo = config.get("seo", {})
    merged_seo = {**seo_defaults, **config_seo}
    # Merge structured_data separately
    merged_seo["structured_data"] = {
        **seo_defaults.get("structured_data", {}),
        **config_seo.get("structured_data", {}),
    }
    config["seo"] = merged_seo

    # Ensure other required sections exist
    config.setdefault("brand", {})
    config.setdefault("navigation", {})
    config.setdefault("auth", {})
    config.setdefault("islands", {})
    config.setdefault("features", {})
    config.setdefault("theme", {})
    config.setdefault("i18n", {"default_language": "en"})
    config.setdefault("domains", {"registry": {}})

    return config


def lightwave_navigation(request: HttpRequest) -> dict[str, Any]:
    """
    Inject navigation and auth data into template context.

    Configuration sources (in priority order):
    1. request.site.settings (database) - recommended for production
    2. settings.LIGHTWAVE_CONFIG (YAML) - legacy/development fallback

    Returns context variables compatible with lightwave-media.site's data-* attribute pattern:
    - header_nav: JSON string of header navigation items (enriched with CMS data)
    - footer_nav: JSON string of footer navigation categories
    - company_info: JSON string of brand/company information
    - auth_config: JSON string of auth configuration
    - auth_state: JSON string of current user's auth state
    - lightwave_config: The raw config dict for template access

    Site.settings JSON schema:
        {
            "brand": {
                "name": "CineOS",
                "description": "Professional video editing.",
                "email": "hello@cineos.io",
                "logo_url": "https://cdn.lightwave-media.ltd/brands/cineos/logo.png",
                "logo_minimal_url": "https://cdn.lightwave-media.ltd/brands/cineos/logomark.png",
            },
            "navigation": {
                "header": [...],
                "footer": [...],
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
                "header": {"variant": "default"},
                "footer": {"variant": "footer-large-01"},
            },
            "features": {
                "use_teams": True,
                "use_subscriptions": False,
            },
            "seo": {
                "title_suffix": " | CineOS",
                "og_image": "...",
            },
            "theme": {
                "light_mode": "light",
                "dark_mode": "dark",
            },
        }
    """
    config = _get_site_config(request)

    navigation = config.get("navigation", {})
    # Auto-populate logo URLs from CDN if not explicitly set
    brand = _get_brand_with_auto_logos(request, config.get("brand", {}))
    config.get("auth", {})
    islands = config.get("islands", {})
    features = config.get("features", {})
    seo = config.get("seo", {})
    theme = config.get("theme", {})

    # Get header nav and enrich with CMS data
    header_nav = navigation.get("header", [])
    enriched_header_nav = _enrich_nav_with_cms(request, header_nav)

    # Favicon config
    favicon = brand.get("favicon", {})

    # Get current site if available
    site = getattr(request, "site", None)

    # Build enhanced auth UI config
    auth_ui_config = _get_auth_ui_config(config)

    # Get all state patterns
    auth_state = _get_auth_state(request)
    cart_state = _get_cart_state(request)
    team_state = _get_team_state(request)
    subscription_state = _get_subscription_state(request)
    notification_state = _get_notification_state(request)
    active_path = _get_active_nav_path(request)

    return {
        # Current site object (for direct access)
        "current_site": site,
        # =================================================================
        # JSON strings for data-* attributes (React islands)
        # =================================================================
        "header_nav": json.dumps(enriched_header_nav),
        "footer_nav": json.dumps(navigation.get("footer", [])),
        "company_info": json.dumps(brand),
        "island_config": json.dumps(islands.get("header", {})),
        # Auth (enhanced)
        "auth_config": json.dumps(auth_ui_config),
        "auth_state": json.dumps(auth_state),
        # State patterns (for header/sidebar islands)
        "cart_state": json.dumps(cart_state),
        "team_state": json.dumps(team_state),
        "subscription_state": json.dumps(subscription_state),
        "notification_state": json.dumps(notification_state),
        "active_path": active_path,
        # =================================================================
        # Raw config dict for template logic
        # =================================================================
        "lightwave_config": config,
        # =================================================================
        # Convenience variables for common template usage
        # =================================================================
        # Brand
        "brand_name": brand.get("name", ""),
        "brand_tagline": brand.get("tagline", brand.get("description", "")),
        "site_title": brand.get("site_title", brand.get("name", "")),
        "title_separator": brand.get("title_separator", " | "),
        # Auth mode (for template conditionals)
        "auth_mode": auth_ui_config.get("mode", "subscription"),
        "show_signup_button": auth_ui_config.get("ui", {}).get("show_signup_button", True),
        "show_login_button": auth_ui_config.get("ui", {}).get("show_login_button", True),
        "show_admin_badge": auth_ui_config.get("ui", {}).get("admin_badge", False),
        # Feature flags
        "use_teams": features.get("use_teams", False),
        "use_subscriptions": features.get("use_subscriptions", False),
        "use_social_login": features.get("use_social_login", False),
        "use_ecommerce": features.get("use_ecommerce", False),
        # SEO defaults
        "default_title_suffix": seo.get("title_suffix", brand.get("title_separator", " | ") + brand.get("name", "")),
        "default_og_image": seo.get("og_image", ""),
        # Theme
        "light_mode": theme.get("light_mode", "light"),
        "dark_mode": theme.get("dark_mode", "dark"),
        "brand_theme": _get_brand_theme(request, config),
        # Favicon URLs (CDN)
        "favicon_ico": favicon.get("ico", ""),
        "favicon_png_32": favicon.get("png_32", ""),
        "favicon_png_16": favicon.get("png_16", ""),
        "favicon_apple_touch": favicon.get("apple_touch", ""),
        "favicon_manifest": favicon.get("manifest", ""),
        # User state (for template conditionals)
        "is_authenticated": auth_state.get("isAuthenticated", False),
        "current_user": auth_state.get("user"),
    }
