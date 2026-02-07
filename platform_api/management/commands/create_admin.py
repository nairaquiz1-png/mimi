from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = "Create default superuser if it doesn't exist"

    def handle(self, *args, **kwargs):
        email = os.getenv("ADMIN_EMAIL", "admin@mimi.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123")

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS("✅ Superuser created"))
        else:
            self.stdout.write("ℹ️ Superuser already exists")
