from django.contrib import admin
from .models import (
    CustomUser,
    ProviderProfile,
    ServiceCategory,
    ProviderService,
    Job,
    Booking,
    JobMilestone,
    ChatRoom,
    Message
)

# ----------------------------
# CustomUser admin
# ----------------------------
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'verification_status')
    list_filter = ('role', 'is_staff', 'is_superuser', 'verification_status')
    search_fields = ('username', 'email', 'phone')
    ordering = ('username',)

# ----------------------------
# ProviderProfile admin
# ----------------------------
@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'slug', 'location', 'rating', 'created_at')
    search_fields = ('user__username', 'slug', 'location')
    ordering = ('user__username',)

# ----------------------------
# ServiceCategory admin
# ----------------------------
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)

# ----------------------------
# ProviderService admin
# ----------------------------
@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price', 'created_at')
    search_fields = ('title', 'provider__user__username', 'category__name')
    list_filter = ('category',)
    ordering = ('provider__user__username', 'title')

# ----------------------------
# Job admin (improved)
# ----------------------------
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'service_title',
        'customer',
        'provider',
        'status',
        'created_at'
    )
    search_fields = (
        'id',
        'service__title',
        'customer__username',
        'service__provider__user__username',
    )
    list_filter = ('status',)
    ordering = ('-created_at',)

    def service_title(self, obj):
        return obj.service.title
    service_title.short_description = "Service"

    def customer(self, obj):
        return obj.customer.username
    customer.short_description = "Customer"

    def provider(self, obj):
        return obj.service.provider.user
    provider.short_description = "Provider"

# ----------------------------
# Booking admin (improved)
# ----------------------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'job_id',
        'customer',
        'provider',
        'service_title',
        'created_at'
    )
    search_fields = (
        'job__id',
        'job__service__title',
        'job__customer__username',
        'job__service__provider__user__username',
    )
    list_filter = ('job__status',)
    ordering = ('-created_at',)

    def job_id(self, obj):
        return obj.job.id
    job_id.short_description = "Job ID"

    def customer(self, obj):
        return obj.job.customer.username
    customer.short_description = "Customer"

    def provider(self, obj):
        return obj.job.service.provider.user
    provider.short_description = "Provider"

    def service_title(self, obj):
        return obj.job.service.title
    service_title.short_description = "Service"

# ----------------------------
# Job Milestones
# ----------------------------
@admin.register(JobMilestone)
class JobMilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'job', 'amount', 'completed', 'created_at')
    search_fields = ('title', 'job__id')
    list_filter = ('completed',)
    ordering = ('-created_at',)

# ----------------------------
# Chat System
# ----------------------------
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'created_at')
    search_fields = ('job__id',)
    readonly_fields = ('created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'created_at', 'read')
    search_fields = ('sender__username', 'room__id', 'text')
    list_filter = ('read',)
    readonly_fields = ('created_at',)
