"""User serializers for Django REST Framework.

These serializers work with any CustomUser model that inherits from BaseCustomUser.
"""

from rest_framework import serializers


def create_user_serializer(user_model, extra_fields: list[str] = None):
    """
    Create a serializer class for the given user model.

    Args:
        user_model: The CustomUser model class
        extra_fields: Additional fields to include beyond the defaults

    Returns:
        A ModelSerializer class for the user model

    Usage:
        from lightwave.auth.serializers import create_user_serializer
        from apps.users.models import CustomUser

        CustomUserSerializer = create_user_serializer(CustomUser)
    """
    base_fields = [
        "id",
        "first_name",
        "last_name",
        "email",
        "avatar_url",
        "get_display_name",
    ]
    if extra_fields:
        base_fields = base_fields + extra_fields

    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = user_model
            fields = base_fields

    return UserSerializer


class BaseUserSerializer(serializers.Serializer):
    """
    A base serializer that works with any user model implementing BaseCustomUser.

    This is useful when you don't have direct access to the model class.
    """

    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    avatar_url = serializers.CharField(read_only=True)
    get_display_name = serializers.CharField(read_only=True)
