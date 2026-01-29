"""Timezone utilities for user preferences."""

from django.utils.translation import gettext


def get_common_timezones() -> list[str]:
    """
    Return a list of 30 common timezones for user selection.

    This is a curated list of commonly used timezones across major regions.
    """
    return [
        "Africa/Cairo",
        "Africa/Johannesburg",
        "Africa/Nairobi",
        "America/Anchorage",
        "America/Argentina/Buenos_Aires",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Mexico_City",
        "America/New_York",
        "America/Sao_Paulo",
        "America/Toronto",
        "Asia/Dubai",
        "Asia/Jerusalem",
        "Asia/Kolkata",
        "Asia/Seoul",
        "Asia/Shanghai",
        "Asia/Singapore",
        "Asia/Tokyo",
        "Australia/Perth",
        "Australia/Sydney",
        "Europe/Athens",
        "Europe/London",
        "Europe/Moscow",
        "Europe/Paris",
        "Pacific/Auckland",
        "Pacific/Fiji",
        "Pacific/Honolulu",
        "Pacific/Tongatapu",
        "UTC",
    ]


def get_timezones_display():
    """
    Return timezone choices suitable for Django form fields.

    Returns an iterator of (value, display) tuples with "Not Set" as first option.
    """
    all_tzs = get_common_timezones()
    return zip([""] + all_tzs, [gettext("Not Set")] + all_tzs, strict=False)
