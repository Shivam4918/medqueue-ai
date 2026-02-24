from django.urls import path
from .views import public_home

app_name = "core"

urlpatterns = [
    path("", public_home, name="home"),
]
