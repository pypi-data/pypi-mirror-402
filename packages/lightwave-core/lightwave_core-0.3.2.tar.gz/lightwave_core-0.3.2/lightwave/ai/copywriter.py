"""
LightWave Media Copywriter Agent

Shared copywriter agent for programmatic use across all LightWave projects.
Mirrors the Claude Code agent in .claude/agents/lightwave-copywriter.md.

Usage:
    from lightwave.ai import get_copywriter_agent
    from apps.ai.types import UserDependencies

    agent = get_copywriter_agent()
    result = await agent.run(
        "Write a hero headline for cineOS",
        deps=UserDependencies(user=user)
    )
"""

from pydantic_ai import Agent

from lightwave.ai.brand_context import BrandContext, get_brand_context


def _build_system_prompt(context: BrandContext) -> str:
    """Build the copywriter system prompt from brand context."""

    voice_models_text = "\n\n".join(
        [
            f"### {vm.name}\n"
            f"**Essence:** {vm.essence}\n"
            f"**When:** {vm.when_to_use}\n"
            f"**Example:** {vm.example}"
            for vm in context.voice_models
        ]
    )

    banned_words_text = ", ".join(context.banned_words)
    never_say_text = "\n".join([f"- {item}" for item in context.never_say])
    always_imply_text = "\n".join([f"- {item}" for item in context.always_imply])
    for_text = "\n".join([f"- {item}" for item in context.explicitly_for])
    not_for_text = "\n".join([f"- {item}" for item in context.explicitly_not_for])

    return f"""# LightWave Copywriter

You are the LightWave Media copywriter. You write copy that earns RESPECT within 5 seconds.
Not inspiration. Not excitement. RESPECT - "This person clearly knows their craft."

## Mission
{context.mission}

## Emotional Target
**Primary emotion:** {context.emotional_target.emotion}
**Translation:** "{context.emotional_target.translation}"
**Time to achieve:** {context.emotional_target.time_to_achieve}

How to earn it:
{chr(10).join(["- " + h for h in context.emotional_target.how_to_earn])}

## Voice Models (Choose based on context, blend as needed)

{voice_models_text}

## Transformation Promise
**Primary:** "{context.transformation.primary}"
**Secondary:** "{context.transformation.secondary}"
**Visceral:** {context.transformation.visceral}

## Anti-Patterns

### Banned Words (NEVER use)
{banned_words_text}

### Never Say
{never_say_text}

### Always Imply
{always_imply_text}

## Audience

### We're FOR:
{for_text}

### We're NOT FOR (repel these):
{not_for_text}

## Writing Standards

- Short paragraphs (2-4 sentences max)
- One idea per paragraph
- Active voice preferred
- Concrete examples over abstract concepts
- Clear over clever
- 8th-grade reading level unless technical context requires otherwise
- Dyslexia-friendly formatting (scannable, clear hierarchy)

## Quality Checklist

Before delivering any copy, verify:
- Earns RESPECT (specific, earned confidence)
- Uses appropriate voice model for context
- Zero banned words
- Short paragraphs (2-4 sentences)
- Active voice
- Clear transformation promise
- Repels wrong audience (hustle culture, dabblers)
- Attracts right audience (serious creatives)
- Accessible and scannable

## Output Format

When delivering copy, structure your response as:

**Context:** [Where/how this is used]
**Voice Model:** [Which you're using]

**Primary Copy:**
[The recommended copy]

**Usage Notes:**
- [Tone guidance]
- [Accessibility notes]

Write with specificity, clarity, and earned confidence.
"""


# Pre-build the system prompt
COPYWRITER_SYSTEM_PROMPT = _build_system_prompt(get_brand_context())


def get_copywriter_agent(model: str | None = None, deps_type: type | None = None) -> Agent:
    """
    Factory for LightWave copywriter agent.

    Args:
        model: The model to use. Defaults to settings.DEFAULT_AGENT_MODEL.
        deps_type: The dependencies type. If None, agent has no deps.

    Returns:
        A pydantic-ai Agent configured for copywriting.
    """
    if model:
        agent_model = model
    else:
        try:
            from django.conf import settings

            agent_model = getattr(settings, "DEFAULT_AGENT_MODEL", "claude-sonnet-4-20250514")
        except ImportError:
            agent_model = "claude-sonnet-4-20250514"

    if deps_type:
        return Agent(
            agent_model,
            instructions=COPYWRITER_SYSTEM_PROMPT,
            retries=2,
            deps_type=deps_type,
        )

    return Agent(
        agent_model,
        instructions=COPYWRITER_SYSTEM_PROMPT,
        retries=2,
    )
