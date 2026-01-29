"""
LightWave Media Brand Context

Dataclasses representing the canonical brand context from:
.claude/reference/LIGHTWAVE_BRAND_CONTEXT.yaml

This module provides programmatic access to brand guidelines for
AI agents and other tooling.
"""

from dataclasses import dataclass, field


@dataclass
class VoiceModel:
    """A copywriting voice model with example and usage guidance."""

    name: str
    essence: str
    when_to_use: str
    example: str


@dataclass
class EmotionalTarget:
    """The primary emotional response we aim to evoke."""

    emotion: str = "RESPECT"
    translation: str = "This person clearly knows their craft"
    time_to_achieve: str = "5 seconds"
    how_to_earn: list[str] = field(
        default_factory=lambda: [
            "Specificity over generality",
            "Earned confidence, not borrowed authority",
            "Industry truth-telling",
            "Details only an insider would know",
        ]
    )


@dataclass
class TransformationPromise:
    """What readers should feel after engaging with LightWave."""

    primary: str = "I have control again"
    secondary: str = "I can focus on what matters"
    visceral: str = (
        "Organized mind. Things cleaner. More effortlessly. "
        "Freeing the mind for processing in parallel. "
        "Thinking clearly for creative work is a drug. "
        "Our apps get you there quicker."
    )


@dataclass
class BrandContext:
    """Complete brand context for LightWave Media copywriting."""

    # Company info
    company_name: str = "LightWave Media LLC"
    tagline: str = "Media Production Meets Technology"

    # Mission
    mission: str = (
        "Empower meaningful visual storytelling and humane technology by mastering "
        "image-making and turning that mastery into sustainable products and services."
    )

    # Voice models
    voice_models: list[VoiceModel] = field(default_factory=list)

    # Emotional target
    emotional_target: EmotionalTarget = field(default_factory=EmotionalTarget)

    # Transformation
    transformation: TransformationPromise = field(default_factory=TransformationPromise)

    # Banned words
    banned_words: list[str] = field(
        default_factory=lambda: [
            "passion",
            "passionate",
            "solutions",
            "leverage",
            "synergy",
            "disrupt",
            "revolutionary",
            "game-changing",
            "creator economy",
            "content creator",
            "influencer",
            "side hustle",
            "AI-powered",
            "the future of",
            "unlock your potential",
            "scale your business",
            "join thousands of creators",
            "transform your",
            "empowers storytellers",
        ]
    )

    # Copy rules
    never_say: list[str] = field(
        default_factory=lambda: [
            "AI does the work for you",
            "No coding required",
            "Even you can build software",
        ]
    )

    always_imply: list[str] = field(
        default_factory=lambda: [
            "Your vision, precisely rendered",
            "Architecture matters. Syntax doesn't.",
            "Built by someone who sees systems, not semicolons",
            "The barrier was never intelligence. It was syntax.",
        ]
    )

    # Audience
    explicitly_for: list[str] = field(
        default_factory=lambda: [
            "Independent and small-team cinematographers",
            "Photographers and multidisciplinary creative entrepreneurs",
            "Creative pros struggling with the money/business side",
            "People so good at their craft they make enough to live, but not move forward",
        ]
    )

    explicitly_not_for: list[str] = field(
        default_factory=lambda: [
            "Hustle culture types (Gary Vee disciples)",
            "Hobbyists and dabblers",
            "Quick-fix seekers wanting overnight formulas",
            "People who measure success in followers/views",
        ]
    )


# Default voice models
DEFAULT_VOICE_MODELS = [
    VoiceModel(
        name="Apple / Jony Ive",
        essence="Reverent of craft and materials",
        when_to_use="Describing care put into product details",
        example=(
            "The way light falls across a face. The weight of a camera in your hands. "
            "These details matter. We built for people who notice."
        ),
    ),
    VoiceModel(
        name="Basecamp / DHH",
        essence="Opinionated, anti-hype, contrarian clarity",
        when_to_use="Calling out industry BS, stating strong positions",
        example=(
            "We don't do growth hacking. We do the work. "
            "No courses. No funnels. Just tools that work and get out of your way."
        ),
    ),
    VoiceModel(
        name="Stripe",
        essence="Technical precision meets warm accessibility",
        when_to_use="Explaining complex systems simply",
        example=(
            "One database. Every project. Every client. Every invoice. "
            "The architecture is invisible. The clarity is not."
        ),
    ),
    VoiceModel(
        name="Notion",
        essence="Calm utility - what tools ENABLE not what they ARE",
        when_to_use="Product descriptions, feature copy",
        example="Your creative business. Orchestrated. Less time in spreadsheets. More time behind the camera.",
    ),
    VoiceModel(
        name="Rick Rubin",
        essence="Sparse, present-tense, meditative, gravitas without ego",
        when_to_use="Philosophy, About page, founder voice",
        example="Clarity. Control. The space to do the work. The tools exist to disappear.",
    ),
]


def get_brand_context() -> BrandContext:
    """Get the default LightWave Media brand context."""
    return BrandContext(voice_models=DEFAULT_VOICE_MODELS)
