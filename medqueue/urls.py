"""
URL configuration for medqueue project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 OTP Authentication routes
    path('api/auth/', include('users.urls')),
    path('api/hospitals/', include('hospitals.urls')), 
    path('api/', include('doctors.urls')),  
    path("api/core/", include("core.urls")), # or combine in single api router
]
