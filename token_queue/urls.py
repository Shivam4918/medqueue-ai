# token_queue/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TokenViewSet, CreateTokenAPIView, TokenBookAPIView, WalkinTokenAPIView

from .views import (
    TokenViewSet,
    CreateTokenAPIView,   # admin/receptionist open create
    TokenBookAPIView,     # patient booking API
    WalkinTokenAPIView,
)

router = DefaultRouter()
router.register("", TokenViewSet, basename="token")

urlpatterns = [
    # Staff/Admin token management (DRF UI)
    path("", include(router.urls)),

    # Old public creation endpoint (phone/patient_id)
    path("create/", CreateTokenAPIView.as_view(), name="token-create"),

    # New patient booking endpoint
    path("book/", TokenBookAPIView.as_view(), name="token-book"),
    path("walkin/", WalkinTokenAPIView.as_view(), name="token-walkin"),
]
