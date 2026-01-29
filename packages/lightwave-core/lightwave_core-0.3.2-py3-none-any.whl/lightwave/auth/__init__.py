"""Authentication utilities and base models for LightWave projects."""

from lightwave.auth.helpers import (
    require_email_confirmation,
    user_has_confirmed_email_address,
    validate_profile_picture,
)
from lightwave.auth.models import BaseCustomUser, get_avatar_filename

__all__ = [
    "BaseCustomUser",
    "get_avatar_filename",
    "validate_profile_picture",
    "require_email_confirmation",
    "user_has_confirmed_email_address",
]
