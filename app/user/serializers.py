"""
Serializers for the user API View
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model"""

    class Meta:
        model = get_user_model()
        fields = ['email', "password", 'name']
        # is_staff and others, can be applied when users create themselves, they can only be applied by the admin
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}
        # write_only means that users can write password, but it won't be returned back to them

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)
