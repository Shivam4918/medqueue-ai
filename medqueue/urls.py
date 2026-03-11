"""
URL configuration for MedQueue project
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.views import LogoutView
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView



# ==============================
# PWA MANIFEST
# ==============================
def manifest(request):
    return JsonResponse({
        "name": "MedQueue AI",
        "short_name": "MedQueue",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#2563eb",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })


# ==============================
# HOME ROUTER
# ==============================
# def home(request):
#     if not request.user.is_authenticated:
#         return render(request, "core/home.html")

#     role = request.user.role

#     if role == "patient":
#         return redirect("/dashboard/patient/")

#     if role == "doctor":
#         from doctors.models import Doctor
#         if Doctor.objects.filter(user=request.user).exists():
#             return redirect("/dashboard/doctor/")
#         return render(request, "errors/no_doctor_profile.html", status=403)

#     if role == "receptionist":
#         return redirect("/dashboard/receptionist/walkin/")

#     if role == "hospital_admin":
#         return redirect("/dashboard/hospital/")

#     return redirect("/logout/")

# Serve media files in development
# ==============================
# ROOT URLS
# ==============================
urlpatterns = [
    # Home
    # path("", include("core.urls")),
    # path("manifest.json", manifest, name="manifest"),
    path("", TemplateView.as_view(template_name="core/home.html"), name="landing"),
    path("portal/", TemplateView.as_view(template_name="core/portal.html"), name="portal"),

    # Admin
    path("admin/", admin.site.urls),
    path("hospitals/", include("hospitals.urls")),

    # Auth (portal-based)
    path("auth/", include("users.urls")),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Dashboards
    path("dashboard/", include("dashboard.urls")),

    # APIs (explicit only)
    path("api/token_queue/", include("token_queue.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/hospitals/", include("hospitals.api_urls")),
    path("api/doctors/", include("doctors.urls")),
    # path("api/core/", include("core.urls")),

    # Analytics
    path("analytics/", include("analytics.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
