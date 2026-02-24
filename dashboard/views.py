# dashboard/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from users.decorators import role_required
from django.contrib import messages

from hospitals.models import Hospital
from doctors.models import Doctor
from token_queue.models import Token
from token_queue.services import estimate_wait_for_token
from patients.services import get_or_create_patient_from_user
from django.db.models import Q

from analytics.reports import (
    total_patients_today,
    tokens_per_doctor,
    peak_opd_hours,
    average_wait_time_minutes,
    no_show_rate,
)

# ======================================================
# 🔐 STAFF / HOSPITAL ADMIN DASHBOARD
# ======================================================

@login_required
@role_required("hospital_admin")
def hospital_dashboard(request):
    hospitals = Hospital.objects.all().order_by("name")
    return render(request, "dashboard/hospital_list.html", {
        "hospitals": hospitals
    })


@login_required
@role_required("hospital_admin")
def hospital_detail_dashboard(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    doctors = Doctor.objects.filter(hospital=hospital).order_by("user__username")

    return render(request, "dashboard/hospital_detail.html", {
        "hospital": hospital,
        "doctors": doctors
    })


@login_required
@role_required("hospital_admin")
def hospital_analytics_dashboard(request, hospital_id):
    total_patients = total_patients_today(hospital_id)
    avg_wait = average_wait_time_minutes(hospital_id)
    peak_hours = peak_opd_hours(hospital_id)
    no_show = no_show_rate(hospital_id)
    doctor_tokens = tokens_per_doctor(hospital_id)

    chart_labels = [str(row["_id"]) for row in peak_hours]
    chart_values = [row["count"] for row in peak_hours]

    context = {
        "total_patients": total_patients,
        "avg_wait": avg_wait,
        "peak_hour": chart_labels[0] if chart_labels else "N/A",
        "no_show_rate": no_show,
        "doctor_stats": [
            {"doctor": row["_id"], "total": row["total_tokens"]}
            for row in doctor_tokens
        ],
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }

    return render(request, "hospitals/admin_dashboard.html", context)


# ======================================================
# 👤 PATIENT DASHBOARD
# ======================================================

@login_required
@role_required("patient")
def patient_dashboard(request):

    if getattr(request.user, "role", None) != "patient":
        return render(request, "patients/not_allowed.html")
    
    patient = get_or_create_patient_from_user(request.user)

    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"]
    ).select_related("doctor", "hospital").first()

    context = {"has_token": False}

    if token:
        # Calculate queue position
        # queue_position = Token.objects.filter(
        #     doctor=token.doctor,
        #     status__in=["waiting", "in_service"],
        #     token_number__lt=token.token_number
        # ).count()

        minutes, eta_dt = estimate_wait_for_token(
            token.doctor.id,
            token.token_number
        )

        people_before = Token.objects.filter(
            doctor=token.doctor,
            status="waiting",
            token_number__lt=token.token_number
        ).count()

        context.update({
            "has_token": True,
            "active_token": token,
            "token_number": token.token_number,
            "doctor_name": token.doctor.name,
            "hospital_name": token.hospital.name,
            "status": token.status.replace("_", " ").title(),
            "estimated_wait": minutes,
            "eta": timezone.localtime(eta_dt),
            "queue_position": people_before,
        })


    return render(request, "patients/home.html", context)


# ======================================================
# 👨‍⚕️ DOCTOR DASHBOARD
# ======================================================

@login_required
@role_required("doctor")
def doctor_dashboard(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(
            request,
            "Doctor profile not found. Please contact hospital admin."
        )
        return render(
            request,
            "errors/no_doctor_profile.html",
            status=403
        )

    return render(
        request,
        "dashboard/doctor_dashboard.html",
        {"doctor": doctor}
    )


@login_required
@role_required("doctor")
def doctor_queue_page(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    return render(
        request,
        "dashboard/doctor_queue.html",
        {"doctor_id": doctor.id}
    )


# ======================================================
# 🧾 RECEPTIONIST DASHBOARD
# ======================================================

@login_required
@role_required("receptionist")
def receptionist_walkin_page(request):
    return render(request, "dashboard/receptionist_walkin.html")


@login_required
@role_required("receptionist")
def receptionist_queue_page(request):
    doctors = Doctor.objects.all().order_by("user__username")
    return render(
        request,
        "dashboard/receptionist_queue.html",
        {"doctors": doctors}
    )
