# platform_api/jobs_serializers.py

from rest_framework import serializers
from .models import Job, Booking, JobMilestone
from .provider_serializers import ProviderServiceSerializer, ProviderProfileSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

# Serializer for Job Milestones
class JobMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMilestone
        fields = ("id", "title", "amount", "completed")


# Serializer for Job
class JobSerializer(serializers.ModelSerializer):
    service = ProviderServiceSerializer(read_only=True)
    provider = ProviderProfileSerializer(read_only=True)
    customer = serializers.StringRelatedField(read_only=True)
    milestones = JobMilestoneSerializer(many=True, read_only=True)  # <-- added

    class Meta:
        model = Job
        fields = '__all__'


# Serializer for Booking
class BookingSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
