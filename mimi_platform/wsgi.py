import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mimi_platform.settings")

application = get_wsgi_application()

# ===============================
# AUTO CREATE SUPERUSER (RENDER)
# ===============================
if os.environ.get("DJANGO_CREATE_SUPERUSER") == "true":
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        email = os.environ.get("ADMIN_EMAIL", "admin@mimi.com")
        password = os.environ.get("ADMIN_PASSWORD", "StrongPassword123")

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                username=email,   # IMPORTANT
                email=email,
                password=password,
            )
            print("✅ Superuser created successfully")
        else:
            print("ℹ️ Superuser already exists")

    except Exception as e:
        print("❌ Superuser creation error:", e)
