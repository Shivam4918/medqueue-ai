from django.shortcuts import render
from hospitals.models import Hospital
from patients.models import Patient
from token_queue.models import Token
from django.utils import timezone


def superadmin_dashboard(request):

    hospitals = Hospital.objects.count()
    patients = Patient.objects.count()

    tokens = Token.objects.filter(
        created_at__date=timezone.now().date()
    ).count()

    return render(
        request,
        "admin/dashboard.html",
        {
            "hospitals": hospitals,
            "patients": patients,
            "tokens": tokens
        }
    )