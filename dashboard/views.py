# dashboard/views.py
from math import sqrt
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from users.decorators import role_required
from django.contrib import messages
from token_queue.services import create_token
from hospitals.models import Hospital
from doctors.models import Doctor
from token_queue.models import Token
from token_queue.services import estimate_wait_for_token
from patients.services import get_or_create_patient_from_user
from django.db.models import Q
from patients.models import Patient

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

    user = request.user

    # Ensure hospital admin
    if user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    # Get hospital for this admin
    hospital = Hospital.objects.filter(admin=user).first()

    if not hospital:
        return render(request, "patients/not_allowed.html")

    # Stats
    total_doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    ).count()

    waiting_tokens = Token.objects.filter(
        hospital=hospital,
        status="waiting"
    ).count()

    in_service_tokens = Token.objects.filter(
        hospital=hospital,
        status="in_service"
    ).count()

    completed_tokens = Token.objects.filter(
        hospital=hospital,
        status="completed"
    ).count()

    context = {
        "hospital": hospital,
        "total_doctors": total_doctors,
        "waiting_tokens": waiting_tokens,
        "in_service_tokens": in_service_tokens,
        "completed_tokens": completed_tokens,
    }

    return render(
        request,
        "hospitals/hospital_dashboard.html",
        context
    )


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
    today = timezone.localdate()
    if getattr(request.user, "role", None) != "patient":
        return render(request, "patients/not_allowed.html")

    patient = get_or_create_patient_from_user(request.user)

    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"],
        booked_at__date=today
    ).select_related("doctor", "hospital").first()

    context = {"has_token": False}

    if token:

        # Current running token
        running_token = Token.objects.filter(
            doctor=token.doctor,
            status="in_service",
            booked_at__date=today
        ).order_by("token_number").first()

        now_serving = running_token.token_number if running_token else None

        # People ahead in queue
        people_before = Token.objects.filter(
            doctor=token.doctor,
            status__in=["waiting","in_service"],
            booked_at__date=today,
            token_number__lt=token.token_number
        ).count()

        # Estimated wait
        minutes, eta_dt = estimate_wait_for_token(
            token.doctor.id,
            token.token_number
        )

        # Total queue length
        queue_length = Token.objects.filter(
            doctor=token.doctor,
            status__in=["waiting","in_service"],
            booked_at__date=today
        ).count()

        # Next tokens in queue
        next_tokens = Token.objects.filter(
            doctor=token.doctor,
            status="waiting",
            booked_at__date=today
        ).order_by("token_number")[:3]
        
        # Nearby hospitals
        hospitals = Hospital.objects.all().order_by("name")[:5]

        # Recent visits (last completed tokens)
        recent_visits = (
            Token.objects
            .filter(
                patient=patient,
                status="completed"
            )
            .select_related("doctor", "hospital")
            .order_by("-booked_at")[:3]
        )
        
        context.update({
            "has_token": True,
            "active_token": token,
            "token_number": token.token_number,
            "doctor_name": token.doctor.name,
            "hospital_name": token.hospital.name,
            "status": token.status.replace("_", " ").title(),

            "now_serving": now_serving,
            "queue_position": people_before + 1,
            "queue_length": queue_length,

            "estimated_wait": minutes,
            "eta": timezone.localtime(eta_dt),

            "next_tokens": [t.token_number for t in next_tokens],
            "hospitals": hospitals,
            "recent_visits": recent_visits
        })

    return render(request, "patients/dashboard.html", context)

@login_required
@role_required("patient")
def profile_view(request):

    patient = get_or_create_patient_from_user(request.user)

    errors = {}

    if request.method == "POST":

        phone = request.POST.get("phone")
        emergency = request.POST.get("emergency_contact")
        dob = request.POST.get("dob")

        # ===============================
        # PHONE VALIDATION
        # ===============================
        if phone:
            if not phone.isdigit() or len(phone) != 10:
                errors["phone"] = "Phone number must be exactly 10 digits."

        # ===============================
        # EMERGENCY CONTACT VALIDATION
        # ===============================
        if emergency:

            if not emergency.isdigit():
                errors["emergency_contact"] = "Emergency contact must contain only numbers."

            elif len(emergency) != 10:
                errors["emergency_contact"] = "Emergency contact must be exactly 10 digits."

            elif emergency[0] not in ["6", "7", "8", "9"]:
                errors["emergency_contact"] = "Mobile number must start with 6, 7, 8, or 9."

        # ===============================
        # DOB VALIDATION
        # ===============================
        if not dob:
            errors["dob"] = "Please enter your date of birth."

        # ===============================
        # SAVE DATA ONLY IF NO ERRORS
        # ===============================
        if not errors:

            patient.phone = phone
            patient.emergency_contact = emergency
            patient.gender = request.POST.get("gender")
            patient.blood_group = request.POST.get("blood_group")
            patient.address = request.POST.get("address")

            if dob:
                patient.date_of_birth = dob

            if request.FILES.get("profile_picture"):
                patient.profile_picture = request.FILES["profile_picture"]

            patient.save()

            messages.success(request, "Profile updated successfully!")

            return redirect("dashboard:profile")

    return render(
        request,
        "patients/profile.html",
        {
            "patient": patient,
            "errors": errors
        }
    )

@login_required
@role_required("patient")
def nearby_hospitals_view(request):

    user_lat = 21.1702
    user_lng = 72.8311

    hospitals = Hospital.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

    hospital_data = []

    for hospital in hospitals:

        distance = sqrt(
            (hospital.latitude - user_lat) ** 2 +
            (hospital.longitude - user_lng) ** 2
        )

        # Simulated queue load (AI prediction later)
        queue_load = random.randint(5, 40)

        estimated_wait = queue_load * 2

        hospital_data.append({
            "hospital": hospital,
            "distance": round(distance * 111, 2),
            "queue_load": queue_load,
            "estimated_wait": estimated_wait
        })

    # Sort by distance
    hospital_data.sort(key=lambda x: x["distance"])

    nearest_hospitals = hospital_data[:5]

    # AI Recommendation (shortest queue)
    recommended = min(nearest_hospitals, key=lambda x: x["queue_load"])

    context = {
        "hospitals": nearest_hospitals,
        "recommended_hospital": recommended
    }

    return render(request, "patients/nearby_hospitals.html", context)

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

# ======================================================
# 📺 QUEUE LIVE VIEW
# ======================================================

@login_required
def queue_live_view(request):

    patient = get_or_create_patient_from_user(request.user)

    today = timezone.localdate()

    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"],
        booked_at__date=today
    ).select_related("doctor", "hospital").first()
    # token = Token.objects.filter(
    #     patient=patient,
    #     status__in=["waiting", "in_service"]
        
    # ).select_related("doctor", "hospital").first()

    if not token:
        return render(request, "patients/queue_live.html", {
            "no_token": True
        })

    # Current running token
    running_token = Token.objects.filter(
        doctor=token.doctor,
        status="in_service"
    ).order_by("token_number").first()

    now_serving = running_token.token_number if running_token else None

    # Patients ahead
    people_before = Token.objects.filter(
        doctor=token.doctor,
        status__in=["waiting", "in_service"],
        token_number__lt=token.token_number
    ).count()

    # Next tokens
    next_tokens = Token.objects.filter(
        doctor=token.doctor,
        status="waiting"
    ).order_by("token_number")[:5]

    context = {
        "hospital": token.hospital,
        "now_serving": now_serving,
        "next_tokens": next_tokens,
        "my_token": token.token_number,
        "position": people_before + 1,
        "patients_ahead": people_before,
    }

    return render(request, "patients/queue_live.html", context)

@login_required
def patient_tokens_view(request):

    tokens = (
        Token.objects
        .filter(patient__user=request.user)
        .select_related("doctor", "hospital")
        .order_by("-created_at")
    )

    return render(
        request,
        "patients/my_tokens.html",
        {
            "tokens": tokens
        }
    )

@login_required
@role_required("patient")
def book_token_view(request):

    hospitals = Hospital.objects.all()
    doctors = Doctor.objects.select_related("hospital")

    patient = get_or_create_patient_from_user(request.user)

    # 🔴 CHECK IF PATIENT ALREADY HAS ACTIVE TOKEN
    existing_token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"]
    ).first()

    if existing_token:
        messages.warning(
            request,
            f"You already have an active token (A-{existing_token.token_number})."
        )
        return redirect("dashboard:patient_dashboard")

    if request.method == "POST":

        hospital_id = request.POST.get("hospital")
        doctor_id = request.POST.get("doctor")

        hospital = Hospital.objects.get(id=hospital_id)
        doctor = Doctor.objects.get(id=doctor_id)

        # Create new token
        token = create_token(
            patient=patient,
            doctor=doctor,
            hospital=hospital
        )

        messages.success(
            request,
            f"Token A-{token.token_number} booked successfully!"
        )

        return redirect("dashboard:patient_dashboard")

    return render(
        request,
        "patients/book_token.html",
        {
            "hospitals": hospitals,
            "doctors": doctors
        }
    )

@login_required
@role_required("patient")
def visit_history_view(request):

    patient = get_or_create_patient_from_user(request.user)

    visits = (
        Token.objects
        .filter(
            patient=patient,
            status="completed"
        )
        .select_related("doctor", "hospital")
        .order_by("-booked_at")
    )

    return render(
        request,
        "patients/visit_history.html",
        {
            "visits": visits
        }
    )

@login_required
def receptionist_dashboard(request):

    if request.user.role != "receptionist":
        return render(request,"patients/not_allowed.html")

    hospital = request.user.hospital

    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )

    total_doctors = doctors.count()

    waiting_tokens = Token.objects.filter(
        hospital=hospital,
        status="waiting"
    ).count()

    in_service_tokens = Token.objects.filter(
        hospital=hospital,
        status="in_service"
    ).count()

    completed_tokens = Token.objects.filter(
        hospital=hospital,
        status="completed"
    ).count()

    context = {
        "total_doctors":total_doctors,
        "waiting_tokens":waiting_tokens,
        "in_service_tokens":in_service_tokens,
        "completed_tokens":completed_tokens
    }

    return render(
        request,
        "receptionist/dashboard.html",
        context
    )