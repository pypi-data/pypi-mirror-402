"""
Hero Section Content Types and Default Content.

This module provides typed content structures for hero sections,
along with the LightWave-voiced default content.

Usage:
    from lightwave.cms.hero import HeroContent, LIGHTWAVE_HERO_CONTENT

    # Get hero from CMS Component model
    component = Component.objects.get(name="homepage-hero", component_type="hero")
    hero = HeroContent(**component.props)

    # Or use default content
    hero = LIGHTWAVE_HERO_CONTENT
"""

from dataclasses import dataclass
from typing import TypedDict


class CTAButton(TypedDict):
    """Call-to-action button configuration."""

    label: str
    href: str
    variant: str  # "primary" | "secondary"
    icon: str | None  # Icon name from @untitledui/icons


class HeroImage(TypedDict):
    """Hero image configuration with CDN support."""

    src: str
    alt: str
    srcDark: str | None  # Dark mode variant
    srcMobile: str | None  # Mobile variant
    srcMobileDark: str | None  # Mobile dark variant


class BadgeConfig(TypedDict):
    """Feature badge configuration."""

    text: str
    addonText: str | None
    href: str | None
    color: str  # "brand" | "gray" | "success" etc.


@dataclass
class HeroContent:
    """
    Complete hero section content.

    This dataclass maps directly to the Component.props JSONField
    for component_type="hero".
    """

    # Core copy
    headline: str
    subheadline: str

    # Badge (optional)
    badge: BadgeConfig | None = None

    # CTAs
    primary_cta: CTAButton | None = None
    secondary_cta: CTAButton | None = None

    # Hero image/mockup
    image: HeroImage | None = None

    # SEO
    meta_title: str | None = None
    meta_description: str | None = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON storage in Component.props."""
        return {
            "headline": self.headline,
            "subheadline": self.subheadline,
            "badge": self.badge,
            "primary_cta": self.primary_cta,
            "secondary_cta": self.secondary_cta,
            "image": self.image,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HeroContent":
        """Create from Component.props dict."""
        return cls(
            headline=data.get("headline", ""),
            subheadline=data.get("subheadline", ""),
            badge=data.get("badge"),
            primary_cta=data.get("primary_cta"),
            secondary_cta=data.get("secondary_cta"),
            image=data.get("image"),
            meta_title=data.get("meta_title"),
            meta_description=data.get("meta_description"),
        )


# =============================================================================
# LIGHTWAVE MEDIA HERO CONTENT
# Voice: Notion-style (calm utility) + Rick Rubin (sparse, meditative)
# Emotional Target: RESPECT in 5 seconds
# =============================================================================

LIGHTWAVE_HERO_CONTENT = HeroContent(
    # Headline: Notion-style - calm utility, what it ENABLES not what it IS
    headline="Your creative business. Orchestrated.",
    # Subheadline: Specific to the pain point, no fluff
    subheadline=(
        "Project management, client workflows, and financial tracking "
        "in one place. Built by a cinematographer who got tired of "
        "duct-taping spreadsheets together."
    ),
    # Badge: Subtle, specific
    badge={
        "text": "Now in beta",
        "addonText": "cineOS",
        "href": "/products/cineos",
        "color": "brand",
    },
    # CTAs: Direct, no urgency manipulation
    primary_cta={
        "label": "Get early access",
        "href": "/signup",
        "variant": "primary",
        "icon": None,
    },
    secondary_cta={
        "label": "See how it works",
        "href": "/demo",
        "variant": "secondary",
        "icon": "PlayCircle",
    },
    # Image: CDN-backed
    image={
        "src": "https://cdn.lightwave-media.ltd/media/marketing/hero/dashboard-light.webp",
        "alt": "cineOS dashboard showing project overview",
        "srcDark": "https://cdn.lightwave-media.ltd/media/marketing/hero/dashboard-dark.webp",
        "srcMobile": "https://cdn.lightwave-media.ltd/media/marketing/hero/dashboard-mobile-light.webp",
        "srcMobileDark": "https://cdn.lightwave-media.ltd/media/marketing/hero/dashboard-mobile-dark.webp",
    },
    # SEO
    meta_title="LightWave Media | Your Creative Business, Orchestrated",
    meta_description=(
        "Project management, client workflows, and financial tracking for "
        "cinematographers and creative professionals. Built by creatives, for creatives."
    ),
)


# Alternative headlines for A/B testing or different contexts
HERO_HEADLINE_VARIANTS = {
    # DHH-style: Opinionated, anti-hype
    "dhh": {
        "headline": "Software for cinematographers. By a cinematographer.",
        "subheadline": (
            "Not a dev who watched a few films. Not a startup that interviewed "
            "some DPs. Twenty years behind the camera, now building the tools "
            "I wish existed."
        ),
    },
    # Rick Rubin-style: Sparse, meditative
    "rubin": {
        "headline": "Clarity. Control. The space to do the work.",
        "subheadline": "The tools exist to disappear. What remains is the craft.",
    },
    # Apple/Jony Ive-style: Reverent of craft
    "apple": {
        "headline": "Every detail considered. Every workflow refined.",
        "subheadline": (
            "We obsess over the small things so you can focus on the big ones. "
            "Shot lists that adapt. Invoices that send themselves. "
            "Time reclaimed for the work that matters."
        ),
    },
    # Stripe-style: Technical precision + warm
    "stripe": {
        "headline": "One system. Every project. Every client.",
        "subheadline": ("From pitch to wrap to payment. The architecture is invisible. " "The clarity is not."),
    },
}
