from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings
from .models import JobMilestone, Escrow, Transaction, Wallet
from .payment_serializers import FundWalletSerializer


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
@method_decorator(csrf_exempt, name='dispatch')
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

from django.http import JsonResponse
from .utils import broadcast_job_location
from .models import Job

def update_job_location(request, job_id):
    """
    Endpoint to update job location and broadcast to WebSocket clients.
    Expects POST data: lat, lng, status
    """
    lat = request.POST.get("lat")
    lng = request.POST.get("lng")
    status = request.POST.get("status", "in_progress")

    # Save to database
    try:
        job = Job.objects.get(id=job_id)
        job.lat = lat
        job.lng = lng
        job.status = status
        job.save()
    except Job.DoesNotExist:
        return JsonResponse({"success": False, "detail": "Job not found"}, status=404)

    # Broadcast to WebSocket
    broadcast_job_location(job_id, lat, lng, status)

    return JsonResponse({"success": True})


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
    
class FundMilestoneView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request, milestone_id):
        user = request.user
        try:
            milestone = JobMilestone.objects.get(id=milestone_id)
            if milestone.funded:
                return Response({"detail": "Milestone already funded."}, status=400)
            if milestone.job.customer != user:
                return Response({"detail": "Not your milestone."}, status=403)
            
            wallet = user.wallet
            if wallet.balance < milestone.amount:
                return Response({"detail": "Insufficient balance."}, status=400)
            
            # Deduct from customer wallet
            wallet.balance -= milestone.amount
            wallet.save()

            # Create escrow
            Escrow.objects.create(
                job=milestone.job,
                milestone=milestone,
                customer=user,
                provider=milestone.job.provider,
                amount=milestone.amount,
            )

            # Mark milestone funded
            milestone.funded = True
            milestone.save()

            # Log transaction
            Transaction.objects.create(
                wallet=wallet,
                transaction_type="debit",
                amount=milestone.amount,
                description=f"Funded milestone {milestone.title} for Job {milestone.job.id}"
            )

            return Response({"detail": "Milestone funded successfully."})
        except JobMilestone.DoesNotExist:
            return Response({"detail": "Milestone not found."}, status=404)

class ReleaseMilestoneView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request, milestone_id):
        user = request.user
        try:
            milestone = JobMilestone.objects.get(id=milestone_id)
            escrow = Escrow.objects.get(milestone=milestone)

            if milestone.job.customer != user:
                return Response({"detail": "You are not the customer for this milestone."}, status=403)

            if escrow.released:
                return Response({"detail": "Escrow already released."}, status=400)

            amount = escrow.amount
            admin_cut = amount * 0.2
            provider_amount = amount * 0.8

            # Update provider wallet
            provider_wallet, _ = Wallet.objects.get_or_create(user=milestone.job.provider.user)
            provider_wallet.balance += provider_amount
            provider_wallet.save()

            # Update admin wallet (single admin user)
            admin_wallet = Wallet.objects.get(user__is_superuser=True)
            admin_wallet.balance += admin_cut
            admin_wallet.save()

            # Mark escrow as released
            escrow.released = True
            escrow.save()

            # Log transactions
            Transaction.objects.create(
                wallet=provider_wallet,
                transaction_type="credit",
                amount=provider_amount,
                description=f"Milestone {milestone.title} released from Job {milestone.job.id}"
            )
            Transaction.objects.create(
                wallet=admin_wallet,
                transaction_type="credit",
                amount=admin_cut,
                description=f"Platform cut for milestone {milestone.title} Job {milestone.job.id}"
            )

            return Response({"detail": "Milestone released successfully."})

        except JobMilestone.DoesNotExist:
            return Response({"detail": "Milestone not found."}, status=404)
        except Escrow.DoesNotExist:
            return Response({"detail": "Escrow record not found."}, status=404)

class SubmitMilestoneWorkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, milestone_id):
        try:
            milestone = JobMilestone.objects.get(id=milestone_id)

            # Ensure the logged-in user is the provider
            if milestone.job.provider.user != request.user:
                return Response(
                    {"detail": "You are not the provider for this job."},
                    status=403
                )

            # Ensure milestone is funded first
            if milestone.status != "funded":
                return Response(
                    {"detail": "Milestone must be funded before submitting work."},
                    status=400
                )

            milestone.status = "submitted"
            milestone.save()

            return Response({"detail": "Work submitted successfully."})

        except JobMilestone.DoesNotExist:
            return Response({"detail": "Milestone not found."}, status=404)
        

# ----------------------------
# Wallet funding (Flutterwave demo)
# ----------------------------

class FundWalletView(APIView):
    """
    Create a Flutterwave payment link for funding wallet.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FundWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        user = request.user

        # Create a pending Transaction
        transaction = Transaction.objects.create(
            wallet=user.wallet,
            transaction_type="credit",
            amount=amount,
            status="pending",
            description="Wallet funding via Flutterwave demo"
        )

        # Make sure FRONTEND_URL exists
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

        payload = {
            "tx_ref": f"wallet-{transaction.id}",
            "amount": float(amount),
            "currency": "NGN",
            "redirect_url": f"{frontend_url}/wallet/fund/callback",
            "payment_options": "card",
            "customer": {
                "email": user.email,
                "phonenumber": getattr(user, "phone", ""),
                "name": f"{user.first_name} {user.last_name}".strip() or user.username,
            },
            "customizations": {
                "title": "Mimi Wallet Fund",
                "description": "Funding your wallet",
            },
        }

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post("https://api.flutterwave.com/v3/payments", json=payload, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            # Log for debugging
            print(f"Flutterwave request failed: {e}")
            return Response({"detail": "Error creating payment link"}, status=500)

        data = response.json()
        if data.get("status") != "success":
            return Response({"detail": "Failed to create payment link"}, status=500)

        payment_link = data["data"]["link"]
        return Response({"payment_link": payment_link})