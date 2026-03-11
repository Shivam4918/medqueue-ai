from django.urls import path
from .views import nearby_hospitals, hospital_detail

urlpatterns = [

    # Nearby hospitals list
    path("nearby/", nearby_hospitals, name="nearby_hospitals"),

    # Hospital detail page
    path("<int:pk>/", hospital_detail, name="hospital_detail"),

]