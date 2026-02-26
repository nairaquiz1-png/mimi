from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.conf import settings

# ----------------------------
# Custom User
# ----------------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Provider'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, default='')
    verification_status = models.BooleanField(default=False)

    def __str__(self):
        return self.username


# ----------------------------
# Provider Profile
# ----------------------------
class ProviderProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'provider'},
        related_name='provider_profile'
    )
    slug = models.SlugField(unique=True, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.user.username)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} Profile"


# ----------------------------
# Service Category
# ----------------------------
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ----------------------------
# Provider Service
# ----------------------------
class ProviderService(models.Model):
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name='services'
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='services'
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('provider', 'category', 'title')

    def __str__(self):
        return f"{self.title} by {self.provider.user.username}"


# ----------------------------
# Job & Booking
# ----------------------------
class Job(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("closed", "Closed"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_jobs",
        limit_choices_to={'role': 'customer'}
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="provider_jobs"
    )
    service = models.ForeignKey(
        ProviderService,
        on_delete=models.CASCADE,
        related_name="jobs"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    scheduled_for = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job #{self.id} ({self.status})"


class Booking(models.Model):
    job = models.OneToOneField(
        Job,
        on_delete=models.CASCADE,
        related_name="booking"
    )
    confirmed = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=50, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for Job #{self.job.id}"


class JobStatusLog(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="status_logs"
    )
    status = models.CharField(max_length=20, choices=Job.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job #{self.job.id} → {self.status}"


class JobMilestone(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {'Done' if self.completed else 'Pending'}"


# ----------------------------
# ChatRoom & Message (Week 5)
# ----------------------------
class ChatRoom(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="chat_room")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatRoom for Job {self.job.id}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} in Room {self.room.id}"
