from rest_framework import viewsets
from .models import Hospital
from .serializers import HospitalSerializer
from .permissions import IsHospitalAdminOrReadOnly

from doctors.models import Doctor
from token_queue.models import Token

from django.shortcuts import render, get_object_or_404


class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    permission_classes = [IsHospitalAdminOrReadOnly]


# ==============================
# Nearby Hospitals Page
# ==============================
def nearby_hospitals(request):

    hospitals = Hospital.objects.all()

    hospital_cards = []

    for hospital in hospitals:

        doctor_count = Doctor.objects.filter(
            hospital=hospital,
            is_active=True
        ).count()

        queue_count = Token.objects.filter(
            hospital=hospital,
            status="waiting"
        ).count()

        # Queue color logic
        if queue_count < 5:
            queue_color = "green"
        elif queue_count < 15:
            queue_color = "orange"
        else:
            queue_color = "red"

        hospital_cards.append({
            "id": hospital.id,
            "name": hospital.name,
            "city": hospital.city,
            "doctor_count": doctor_count,
            "queue_count": queue_count,
            "queue_color": queue_color,
        })

    # Sort hospitals by queue size (best hospitals first)
    hospital_cards = sorted(
        hospital_cards,
        key=lambda x: x["queue_count"]
    )

    return render(
        request,
        "hospitals/nearby_hospitals.html",
        {"hospitals": hospital_cards}
    )


# ==============================
# Hospital Detail Page
# ==============================
def hospital_detail(request, pk):

    hospital = get_object_or_404(Hospital, pk=pk)

    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )

    return render(
        request,
        "hospitals/hospital_detail.html",
        {
            "hospital": hospital,
            "doctors": doctors
        }
    )