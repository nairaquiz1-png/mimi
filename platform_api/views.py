from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

from .models import (
    ChatRoom,
    Message,
    ProviderProfile,
    ProviderService,
    Job,
    Booking,
    JobMilestone
)
from .chat_serializers import ChatRoomSerializer, MessageSerializer
from .provider_serializers import ProviderProfileSerializer, ProviderServiceSerializer
from .jobs_serializers import JobSerializer, BookingSerializer, JobMilestoneSerializer
from .user_serializers import RegisterSerializer, UserSerializer
from .permissions import IsProvider, IsCustomer

User = get_user_model()

# ----------------------------
# User Registration / Auth
# ----------------------------
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# ----------------------------
# Role-based views
# ----------------------------
class ProviderOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsProvider]

    def get(self, request):
        return Response({"message": "Hello Provider 👋"})


class CustomerOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        return Response({"message": "Hello Customer 👋"})


# ----------------------------
# Provider endpoints (PUBLIC - Marketplace browsing)
# ----------------------------
class ProviderListView(generics.ListAPIView):
    queryset = ProviderProfile.objects.all()
    serializer_class = ProviderProfileSerializer
    permission_classes = [AllowAny]


class ProviderDetailView(generics.RetrieveAPIView):
    queryset = ProviderProfile.objects.all()
    serializer_class = ProviderProfileSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]


# ----------------------------
# Provider services (PUBLIC - Needed for frontend listing)
# ----------------------------
class ProviderServiceListView(generics.ListAPIView):
    queryset = ProviderService.objects.all()
    serializer_class = ProviderServiceSerializer
    permission_classes = [AllowAny]


# ----------------------------
# Jobs & Bookings (AUTH REQUIRED)
# ----------------------------
class JobListCreateView(generics.ListCreateAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Job.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        job = serializer.save(customer=self.request.user)

        # Auto-create default milestones
        default_milestones = [
            {"title": "Initial Assessment", "amount": 0},
            {"title": "Work In Progress", "amount": 0},
            {"title": "Final Review", "amount": 0},
        ]
        for m in default_milestones:
            JobMilestone.objects.create(
                job=job,
                title=m["title"],
                amount=m["amount"],
                completed=False
            )


class JobDetailView(generics.RetrieveUpdateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "provider":
            return Booking.objects.filter(job__service__provider__user=user)
        return Booking.objects.filter(job__customer=user)


# ----------------------------
# Milestone completion toggle (Provider only)
# ----------------------------
class JobMilestoneUpdateView(generics.UpdateAPIView):
    queryset = JobMilestone.objects.all()
    serializer_class = JobMilestoneSerializer
    permission_classes = [IsAuthenticated, IsProvider]

    def perform_update(self, serializer):
        milestone = serializer.save()
        job = milestone.job
        if all(m.completed for m in job.milestones.all()):
            job.status = "completed"
            job.save()


# ----------------------------
# Chat
# ----------------------------
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        job_id = self.kwargs["room_id"]
        room, _ = ChatRoom.objects.get_or_create(job_id=job_id)
        return Message.objects.filter(room=room)


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        job_id = self.kwargs["room_id"]
        room, _ = ChatRoom.objects.get_or_create(job_id=job_id)
        serializer.save(sender=self.request.user, room=room)


class ChatRoomListView(generics.ListAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(job__customer=user) | ChatRoom.objects.filter(job__service__provider__user=user)
