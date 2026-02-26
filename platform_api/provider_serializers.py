from rest_framework import serializers
from .models import ProviderProfile, ServiceCategory, ProviderService
from django.contrib.auth import get_user_model

User = get_user_model()

# Provider User Serializer
class ProviderUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'role')

# Provider Profile Serializer
class ProviderProfileSerializer(serializers.ModelSerializer):
    user = ProviderUserSerializer(read_only=True)
    services = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = ProviderProfile
        fields = ('id', 'user', 'slug', 'bio', 'location', 'rating', 'services')

# Service Category Serializer
class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ('id', 'name', 'description')

# Provider Service Serializer
class ProviderServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)

    class Meta:
        model = ProviderService
        fields = ('id', 'title', 'description', 'price', 'category', 'provider')
