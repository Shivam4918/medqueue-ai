# dashboard/views.py
from math import sqrt
import random
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from users.models import Notification
from patients.services import check_and_notify_queue
from users.decorators import role_required
from django.contrib import messages
from token_queue.services import create_token
from hospitals.models import Hospital
from doctors.models import Doctor
from token_queue.models import Token
from token_queue.services import estimate_wait_for_token
from patients.services import get_or_create_patient_from_user
from token_queue.realtime import broadcast_queue_update
from django.db.models import Q
from patients.models import Patient
from django.core.paginator import Paginator

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

    # Greeting based on time
    hour = datetime.now().hour

    if hour < 12:
        greeting = "Good Morning"
    elif hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    if getattr(request.user, "role", None) != "patient":
        return render(request, "patients/not_allowed.html")

    patient = get_or_create_patient_from_user(request.user)

    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"],
        booked_at__date=today
    ).select_related("doctor", "hospital").first()

    context = {
        "has_token": False,
        "greeting": greeting
    }

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
                status__in=["completed","skipped"]
            )
            .select_related("doctor","hospital")
            .order_by("-booked_at")[:3]
        )
        
        context.update({
            "has_token": True,
            "active_token": token,
            "display_token": token.display_token,
            "doctor_name": token.doctor.name,
            "hospital_name": token.hospital.name,
            "status": token.status.replace("_", " ").title(),

            "now_serving_display": running_token.display_token if running_token else None,
            "queue_position": people_before + 1,
            "queue_length": queue_length,

            "estimated_wait": minutes,
            "eta": timezone.localtime(eta_dt),

            "next_tokens": [t.display_token for t in next_tokens],
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

    doctor = Doctor.objects.filter(user=request.user).first()

    tokens = Token.objects.filter(
        doctor=doctor,
        status__in=["waiting", "in_service"]
    ).order_by("token_number")

    today_tokens = Token.objects.filter(doctor=doctor).count()

    waiting_tokens = Token.objects.filter(
        doctor=doctor,
        status="waiting"
    ).count()

    serving = Token.objects.filter(
        doctor=doctor,
        status="in_service"
    ).first()

    context = {
        "tokens": tokens,
        "today_tokens": today_tokens,
        "waiting_tokens": waiting_tokens,
        "serving_token": serving.token_number if serving else None
    }

    return render(request, "doctors/doctor_dashboard.html", context)


@login_required
@role_required("doctor")
def doctor_queue_page(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    return render(
        request,
        "dashboard/doctor_queue.html",
        {"doctor_id": doctor.id}
    )

@login_required
def doctor_call_token(request, token_id):

    token = get_object_or_404(Token, id=token_id)

    token.status = "in_service"
    token.called_at = timezone.now()
    token.save()

    Notification.objects.create(
        user=token.patient.user,
        message=f"Your token {token.display_token} has been called by Dr. {token.doctor.name}."
    )

    # check next patients
    check_and_notify_queue(token)

    return redirect("dashboard:doctor_dashboard")


@login_required
def doctor_complete_token(request, token_id):

    token = get_object_or_404(Token, id=token_id)

    token.status = "completed"
    token.save()

    Notification.objects.create(
        user=token.patient.user,
        message=f"Your consultation for token {token.display_token} is completed."
    )

    check_and_notify_queue(token)

    return redirect("dashboard:doctor_dashboard")


@login_required
def doctor_skip_token(request, token_id):

    token = get_object_or_404(Token, id=token_id)

    token.status = "skipped"
    token.updated_at = timezone.now()

    token.save(update_fields=["status","updated_at"])

    Notification.objects.create(
        user=token.patient.user,
        message=f"You missed your token {token.display_token}. Please contact reception."
    )

    check_and_notify_queue(token)

    return redirect("dashboard:doctor_dashboard")

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

    now_serving = running_token.display_token if running_token else None

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
        "my_token": token.display_token,
        "position": people_before + 1,
        "patients_ahead": people_before,
    }

    return render(request, "patients/queue_live.html", context)

@login_required
def patient_tokens_view(request):

    tokens = (
        Token.objects
        .filter(
            patient__user=request.user,
            status__in=["waiting", "in_service"]
        )
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

    patient = get_or_create_patient_from_user(request.user)

    hospitals = Hospital.objects.all().order_by("name")

    # 🔴 prevent multiple active tokens
    existing_token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"]
    ).first()

    if existing_token:
        messages.warning(
            request,
           f"You already have an active token ({existing_token.display_token})."
        )
        return redirect("dashboard:patient_dashboard")

    if request.method == "POST":

        hospital_id = request.POST.get("hospital")
        doctor_id = request.POST.get("doctor")

        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            messages.error(request, "Invalid hospital selected.")
            return redirect("dashboard:book_token")

        try:
            doctor = Doctor.objects.get(
                id=doctor_id,
                hospital=hospital,
                is_active=True
            )
        except Doctor.DoesNotExist:
            messages.error(request, "Invalid doctor selection.")
            return redirect("dashboard:book_token")

        # 🔴 OPD time validation
        now = timezone.localtime().time()

        if doctor.opd_start and doctor.opd_end:
            if not (doctor.opd_start <= now <= doctor.opd_end):
                messages.error(
                    request,
                    "Doctor OPD hours are over. Please select another doctor."
                )
                return redirect("dashboard:book_token")

        # ✅ create token
        token = create_token(
            patient=patient,
            doctor=doctor,
            hospital=hospital,
            priority=0,
            source="online"
        )

        messages.success(
            request,
            f"Token {token.display_token} booked successfully!"
        )

        return redirect("dashboard:patient_dashboard")

    return render(
        request,
        "patients/book_token.html",
        {
            "hospitals": hospitals
        }
    )

@login_required
@role_required("patient")
def visit_history_view(request):

    patient = get_or_create_patient_from_user(request.user)

    visits = (
        Token.objects
        .filter(patient=patient)
        .filter(Q(status="completed") | Q(status="skipped"))
        .select_related("doctor","hospital")
        .order_by("-updated_at","-booked_at")
    )

    paginator = Paginator(visits, 7)   # 5 visits per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "patients/visit_history.html",
        {
            "page_obj": page_obj
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

@login_required
@role_required("patient")
def view_token_page(request, token_id):

    patient = get_or_create_patient_from_user(request.user)

    token = get_object_or_404(
        Token.objects.select_related("doctor", "hospital"),
        id=token_id,
        patient=patient
    )

    return render(
        request,
        "patients/token_slip.html",
        {
            "token": token
        }
    )

from django.http import JsonResponse
from django.utils import timezone

@login_required
def patient_queue_status(request):

    patient = get_or_create_patient_from_user(request.user)

    today = timezone.localdate()

    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting","in_service"],
        booked_at__date=today
    ).select_related("doctor").first()

    if not token:
        return JsonResponse({
            "has_token": False
        })

    running_token = Token.objects.filter(
        doctor=token.doctor,
        status="in_service",
        booked_at__date=today
    ).order_by("token_number").first()

    now_serving = running_token.token_number if running_token else None

    people_before = Token.objects.filter(
        doctor=token.doctor,
        status__in=["waiting","in_service"],
        token_number__lt=token.token_number,
        booked_at__date=today
    ).count()

    minutes, eta_dt = estimate_wait_for_token(
        token.doctor.id,
        token.token_number
    )

    return JsonResponse({
        "has_token": True,
        "display_token": token.display_token,
        "now_serving_display": running_token.display_token if running_token else None,
        "position": people_before + 1,
        "estimated_wait": minutes
    })