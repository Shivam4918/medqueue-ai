#medqueue/urls.py

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
from token_queue.views import track_token_view
from dashboard.views import super_admin_dashboard


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


urlpatterns = [

     # ✅ YOUR CUSTOM ADMIN DASHBOARD (ADD THIS FIRST)
    path("admin/dashboard/", super_admin_dashboard),

    # Landing Page
    path("", TemplateView.as_view(template_name="core/home.html"), name="landing"),

    # Staff portal selection page
    path("portal/", TemplateView.as_view(template_name="core/portal.html"), name="portal"),

    # Core custom routes (Super admin dashboard)
    

    # Django admin (default)
    path("admin/", admin.site.urls),

    # Hospitals
    path("hospitals/", include("hospitals.urls")),

    # Auth
    path("auth/", include("users.urls")),
    path("logout/", LogoutView.as_view(), name="logout"),

    # Dashboards
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("django.contrib.auth.urls")),

    # APIs
    path("api/token_queue/", include("token_queue.urls")),
    path("api/patients/", include("patients.urls")),
    path("api/hospitals/", include("hospitals.api_urls")),
    path("api/doctors/", include("doctors.urls")),

    # Analytics
    path("analytics/", include("analytics.urls")),

    # direct track the token 
    path("track/<int:token_id>/", track_token_view),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
