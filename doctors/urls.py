from rest_framework.routers import DefaultRouter
from .views import DoctorViewSet

router = DefaultRouter()
router.register(r"doctors", DoctorViewSet, basename="doctor")

urlpatterns = router.urls
