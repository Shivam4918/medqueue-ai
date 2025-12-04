# token_queue/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TokenViewSet, CreateTokenAPIView

router = DefaultRouter()
router.register("", TokenViewSet, basename="token")

urlpatterns = [
    path("", include(router.urls)),      # /api/token_queue/  -> token list/manage via DRF router
    path("book/", CreateTokenAPIView.as_view(), name="token-book"),  # /api/token_queue/book/
]
