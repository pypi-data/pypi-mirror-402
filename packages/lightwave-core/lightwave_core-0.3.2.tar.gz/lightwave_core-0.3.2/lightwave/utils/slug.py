"""Utilities for generating unique slugs."""

from django.utils.text import slugify


def get_next_unique_slug(model_class, display_name: str, slug_field_name: str, extra_filter_args: dict = None) -> str:
    """
    Get the next unique slug based on a display name.

    Generates a slug from display_name and appends -2, -3, etc. until unique.

    Args:
        model_class: The Django model class to check against
        display_name: The name to slugify
        slug_field_name: The name of the slug field on the model
        extra_filter_args: Additional filter kwargs for uniqueness check

    Returns:
        A unique slug string
    """
    base_value = slugify(display_name)
    return get_next_unique_slug_value(model_class, base_value, slug_field_name, extra_filter_args)


def get_next_unique_slug_value(
    model_class, slug_value: str, slug_field_name: str, extra_filter_args: dict = None
) -> str:
    """
    Get the next unique slug based on a pre-slugified value.

    Appends -2, -3, etc. until a unique value is found.

    Args:
        model_class: The Django model class to check against
        slug_value: The base slug value
        slug_field_name: The name of the slug field on the model
        extra_filter_args: Additional filter kwargs for uniqueness check

    Returns:
        A unique slug string
    """
    extra_filter_args = extra_filter_args or {}
    filter_kwargs = extra_filter_args.copy()
    filter_kwargs[slug_field_name] = slug_value

    if model_class.objects.filter(**filter_kwargs).exists():
        suffix = 2
        while True:
            next_slug = get_next_slug(slug_value, suffix)
            filter_kwargs[slug_field_name] = next_slug
            if not model_class.objects.filter(**filter_kwargs).exists():
                return next_slug
            suffix += 1
    return slug_value


def get_next_slug(base_value: str, suffix: int, max_length: int = 100) -> str:
    """
    Generate a suffixed slug that won't exceed max_length.

    Args:
        base_value: The base slug string
        suffix: The numeric suffix to append
        max_length: Maximum allowed length for the final slug

    Returns:
        A slug in the format "base-suffix"

    Raises:
        ValueError: If suffix is too long to create a valid slug
    """
    suffix_length = len(str(suffix)) + 1  # +1 for the "-" character
    if suffix_length >= max_length:
        raise ValueError(f"Suffix {suffix} is too long to create a unique slug!")

    return f"{base_value[: max_length - suffix_length]}-{suffix}"
