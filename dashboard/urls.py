# dashboard/urls.py
from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from .views import DashboardHomeView, HospitalDetailView

app_name = "dashboard"

urlpatterns = [
    # auth
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    # dashboard home -> hospitals list
    path("", DashboardHomeView.as_view(), name="home"),

    # hospital detail (doctors list for that hospital)
    path("hospital/<int:pk>/", HospitalDetailView.as_view(), name="hospital-detail"),
]
