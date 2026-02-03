"""
URL configuration for medqueue project.
"""
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import admin
from django.urls import path, include


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

def home(request):
    if not request.user.is_authenticated:
        return redirect("/dashboard/login/")

    role = getattr(request.user, "role", None)

    if role == "patient":
        return redirect("/dashboard/patient/")
    if role == "doctor":
        return redirect("/dashboard/doctor/")
    if role == "receptionist":
        return redirect("/dashboard/receptionist/walkin/")

    # admin / staff
    return redirect("/dashboard/")


urlpatterns = [
    path("", home, name="home"),
    path('admin/', admin.site.urls),
    path("dashboard/", include("dashboard.urls")), 
    path("api/token_queue/", include("token_queue.urls")),
    path('api/auth/', include('users.urls')),
    path("api/patients/", include("patients.urls")),
    path('api/hospitals/', include('hospitals.urls')), 
    path("api/doctors/", include("doctors.urls")), 
    path("api/core/", include("core.urls")), 
    path("dashboard/", include("dashboard.urls")),
    path("manifest.json", manifest, name="manifest"),


    # or combine in single api router
]


