from django.urls import path
from .views import (
    RegisterView,
    MeView,
    ProviderListView,
    ProviderDetailView,
    ProviderServiceListView,
    JobListCreateView,
    JobDetailView,
    BookingListCreateView,
    JobMilestoneUpdateView,
    MessageListView,
    MessageCreateView,
    ChatRoomListView,
    ProviderOnlyView,
    CustomerOnlyView,
)

urlpatterns = [
    # ----------------------------
    # Auth
    # ----------------------------
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),

    # ----------------------------
    # Role-based
    # ----------------------------
    path("provider-only/", ProviderOnlyView.as_view(), name="provider-only"),
    path("customer-only/", CustomerOnlyView.as_view(), name="customer-only"),

    # ----------------------------
    # Providers
    # ----------------------------
    path("providers/", ProviderListView.as_view(), name="provider-list"),
    path("providers/<slug:slug>/", ProviderDetailView.as_view(), name="provider-detail"),
    path("provider-services/", ProviderServiceListView.as_view(), name="provider-service-list"),

    # ----------------------------
    # Jobs & Bookings
    # ----------------------------
    path("jobs/", JobListCreateView.as_view(), name="job-list-create"),
    path("jobs/<int:pk>/", JobDetailView.as_view(), name="job-detail"),
    path("bookings/", BookingListCreateView.as_view(), name="booking-list-create"),
    path("milestones/<int:pk>/", JobMilestoneUpdateView.as_view(), name="milestone-update"),

    # ----------------------------
    # Chat
    # ----------------------------
    path("chat/rooms/", ChatRoomListView.as_view(), name="chat-rooms"),
    path("chat/rooms/<int:room_id>/messages/", MessageListView.as_view(), name="message-list"),
    path("chat/rooms/<int:room_id>/messages/send/", MessageCreateView.as_view(), name="message-create"),
]
