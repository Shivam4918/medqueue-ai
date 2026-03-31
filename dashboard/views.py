# dashboard/views.py
from math import sqrt
import random
import json
from django.contrib.auth import get_user_model
from token_queue.models import ActivityLog
from django.utils.dateparse import parse_date
from django.db.models import Count
from django.contrib.auth import update_session_auth_hash
from django.db.models import Avg, Count, F
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import now
from users.models import Notification

from django.contrib.auth.hashers import check_password, make_password
from patients.services import check_and_notify_queue
from users.decorators import role_required
from django.contrib import messages
from users.forms import ReceptionistProfileForm
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

from analytics.ai_engine import predict_rush, train_model
from django.core.cache import cache
from django.contrib.admin.views.decorators import staff_member_required

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

    # ✅ GET TODAY DATE
    today = timezone.localdate()

    # ===============================
    # 📊 STATS (TODAY BASED)
    # ===============================

    total_doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    ).count()

    waiting_tokens = Token.objects.filter(
        hospital=hospital,
        status="waiting",
        booked_at__date=today   # ✅ FIX
    ).count()

    in_service_tokens = Token.objects.filter(
        hospital=hospital,
        status="in_service",
        booked_at__date=today   # ✅ FIX
    ).count()

    completed_tokens = Token.objects.filter(
        hospital=hospital,
        status="completed",
        booked_at__date=today   # ✅ IMPORTANT FIX
    ).count()

    # ===============================
    # CONTEXT
    # ===============================
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

from analytics.ai_engine import predict_rush  # ✅ ADD THIS IMPORT

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

    # ======================================================
    # 🧠 AI RUSH ALERT (SAFE ADDITION)
    # ======================================================
    try:
        # choose hospital (priority: active token → else first hospital)
        hospital = token.hospital if token else Hospital.objects.first()

        train_model(hospital)

        cache_key = f"ai_{hospital.id}"

        ai_data = cache.get(cache_key)

        if not ai_data:
            ai_data = predict_rush(hospital)
            cache.set(cache_key, ai_data, 300)  # 5 minutes

        if ai_data:
            best_hour = ai_data["best_hour"]

            # format time nicely
            best_time = f"{best_hour}:00 - {best_hour + 1}:00"

            today_count = Token.objects.filter(
                hospital=hospital,
                booked_at__date=today
            ).count()

            raw_growth = (
                (ai_data["total_load"] - today_count) / max(today_count, 5)
            ) * 100

            # clamp value to realistic range
            growth = max(5, min(int(raw_growth), 80))   
            
                # 🔥 ADD THIS BLOCK HERE
            if growth > 60:
                level = "High Rush"
            elif growth > 30:
                level = "Moderate Rush"
            else:
                level = "Low Rush"

            context["ai_alert"] = {
                "growth": max(growth, 10),
                "hospital": hospital.name,
                "best_time": best_time,
                "level": level 
            }
        else:
            context["ai_alert"] = None

    except Exception as e:
        # fallback safety (never break UI)
        context["ai_alert"] = None

    # ======================================================
    # 🔁 YOUR EXISTING LOGIC (UNCHANGED)
    # ======================================================

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

        # Recent visits
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

    now = timezone.localtime().time()

    # ✅ SMART STATUS
    is_available = (
        doctor.opd_start <= now <= doctor.opd_end
        and not doctor.is_paused
    )

    tokens = Token.objects.filter(
        doctor=doctor,
        status__in=["waiting", "in_service"]
    ).order_by("token_number")

    # ✅ TOTAL (ALL TIME)
    total_tokens = Token.objects.filter(doctor=doctor).count()

    # ✅ TODAY ONLY
    today_tokens = Token.objects.filter(
        doctor=doctor,
        booked_at__date=timezone.localdate()
    ).count()

    waiting_tokens = Token.objects.filter(
        doctor=doctor,
        status="waiting"
    ).count()

    serving = Token.objects.filter(
        doctor=doctor,
        status="in_service"
    ).first()

    context = {
        "doctor": doctor,
        "tokens": tokens,
        "total_tokens": total_tokens,
        "today_tokens": today_tokens,
        "waiting_tokens": waiting_tokens,
        "serving_token": serving.display_token if serving else None,
        "is_available": is_available
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

@login_required
@role_required("doctor")
def doctor_call_next(request):

    doctor = Doctor.objects.filter(user=request.user).first()

    next_token = Token.objects.filter(
        doctor=doctor,
        status="waiting"
    ).order_by("token_number").first()

    if next_token:

        next_token.status = "in_service"
        next_token.called_at = timezone.now()
        next_token.save()

        Notification.objects.create(
            user=next_token.patient.user,
            message=f"Your token {next_token.display_token} has been called."
        )

    return redirect("dashboard:doctor_dashboard")

@login_required
@role_required("doctor")
def doctor_profile_view(request):

    doctor = Doctor.objects.filter(user=request.user).first()

    if request.method == "POST":

        action = request.POST.get("action")

        # =========================
        # UPDATE PROFILE
        # =========================
        if action == "update_profile":

            doctor.name = request.POST.get("name")
            doctor.speciality = request.POST.get("speciality")
            doctor.opd_start = request.POST.get("opd_start")
            doctor.opd_end = request.POST.get("opd_end")

            if request.FILES.get("profile_picture"):
                doctor.profile_picture = request.FILES["profile_picture"]

            doctor.save()

            messages.success(request, "Profile updated successfully")

        # =========================
        # CHANGE PASSWORD
        # =========================
        elif action == "change_password":

            current = request.POST.get("current_password")
            new = request.POST.get("new_password")
            confirm = request.POST.get("confirm_password")

            if not check_password(current, request.user.password):
                messages.error(request, "Current password incorrect")

            elif new != confirm:
                messages.error(request, "Passwords do not match")

            elif len(new) < 8:
                messages.error(request, "Password must be at least 8 characters")

            else:
                request.user.password = make_password(new)
                request.user.save()

                update_session_auth_hash(request, request.user)

                messages.success(request, "Password updated successfully")

        return redirect("dashboard:doctor_profile")

    return render(
        request,
        "doctors/profile.html",
        {"doctor": doctor}
    )

@login_required
@role_required("doctor")
def doctor_analytics(request):

    doctor = Doctor.objects.get(user=request.user)

    tokens = Token.objects.filter(doctor=doctor)

    total_today = tokens.filter(created_at__date=datetime.today()).count()
    completed = tokens.filter(status="completed").count()
    waiting = tokens.filter(status="waiting").count()
    in_service = tokens.filter(status="in_service").count()

    # Recent tokens
    recent_tokens = tokens.order_by("-id")[:5]

    # Hourly data
    hourly = (
        tokens
        .extra({'hour': "HOUR(created_at)"})
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )

    hours = [str(x['hour']) for x in hourly]
    hourly_data = [x['count'] for x in hourly]

    context = {
        "total_today": total_today,
        "completed": completed,
        "waiting": waiting,
        "in_service": in_service,
        "recent_tokens": recent_tokens,
        "hours": hours,
        "hourly_data": hourly_data,
    }

    return render(request, "doctors/analytics.html", context)

@login_required
@role_required("doctor")
def doctor_patient_history(request):

    doctor = Doctor.objects.filter(user=request.user).first()

    # ✅ INCLUDE COMPLETED + SKIPPED
    tokens = (
        Token.objects
        .filter(
            doctor=doctor,
            status__in=["completed", "skipped"]   # ✅ FIX
        )
        .select_related("patient", "hospital")
        .order_by("-updated_at", "-booked_at")
    )

    # ✅ TODAY CALCULATION (BOTH TYPES)
    today = timezone.localdate()

    completed_today = Token.objects.filter(
        doctor=doctor,
        status="completed",
        updated_at__date=today
    ).count()

    skipped_today = Token.objects.filter(
        doctor=doctor,
        status="skipped",
        updated_at__date=today
    ).count()

    paginator = Paginator(tokens, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "doctors/patient_history.html",
        {
            "page_obj": page_obj,
            "completed_today": completed_today,
            "skipped_today": skipped_today   # ✅ OPTIONAL (for UI)
        }
    )

@login_required
@role_required("doctor")
def doctor_queue_view(request):

    doctor = Doctor.objects.filter(user=request.user).first()

    tokens = (
        Token.objects
        .filter(
            doctor=doctor,
            status__in=["waiting", "in_service"]
        )
        .select_related("patient")
        .order_by("token_number")
    )

    now_serving = tokens.filter(status="in_service").first()

    waiting_count = tokens.filter(status="waiting").count()

    next_patient = tokens.filter(status="waiting").first()

    context = {
        "tokens": tokens,
        "now_serving": now_serving,
        "waiting_count": waiting_count,
        "next_patient": next_patient
    }

    return render(
        request,
        "doctors/my_queue.html",
        context
    )

@login_required
@role_required("doctor")
def doctor_toggle_queue(request):

    doctor = Doctor.objects.get(user=request.user)

    doctor.is_paused = not doctor.is_paused
    doctor.save()

    return redirect("dashboard:doctor_dashboard")

@login_required
@role_required("doctor")
def doctor_delay_notification(request):

    doctor = Doctor.objects.get(user=request.user)

    tokens = Token.objects.filter(
        doctor=doctor,
        status="waiting"
    )

    for token in tokens:
        Notification.objects.create(
            user=token.patient.user,
            message=f"Dr. {doctor.name} is delayed. Please wait."
        )

    return redirect("dashboard:doctor_dashboard")

# ======================================================
# 🧾 RECEPTIONIST DASHBOARD
# ======================================================

@login_required
@role_required("receptionist")
def receptionist_walkin_page(request):
    doctors = Doctor.objects.filter(
        hospital=request.user.hospital,
        is_active=True
    )
    return render(request, "receptionist/walkin.html", {
        "doctors": doctors
    })

@login_required
@role_required("receptionist")
def receptionist_queue_page(request):

    hospital = request.user.hospital

    tokens = Token.objects.filter(
        hospital=hospital,
        status__in=["waiting", "in_service"]
    ).select_related("patient", "doctor").order_by("token_number")

    # 🟢 CURRENT TOKEN
    current_token = tokens.filter(status="in_service").first()

    # 🟡 NEXT TOKENS
    if current_token:
        next_tokens = tokens.filter(
            status="waiting",
            token_number__gt=current_token.token_number
        ).order_by("token_number")
    else:
        next_tokens = tokens.filter(
            status="waiting"
        ).order_by("token_number")

    # ✅ ADD THIS LINE HERE
    next_tokens = next_tokens[:5]

    context = {
        "tokens": tokens,
        "current_token": current_token,
        "next_tokens": next_tokens,
    }

    return render(request, "receptionist/queue.html", context)

@login_required
@role_required("receptionist")
def doctor_list_view(request):

    hospital = request.user.hospital

    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )

    now = timezone.localtime().time()

    doctor_data = []

    for doc in doctors:

        waiting_count = Token.objects.filter(
            doctor=doc,
            status="waiting"
        ).count()

        serving = Token.objects.filter(
            doctor=doc,
            status="in_service"
        ).first()

        # ✅ SMART STATUS LOGIC
        is_available = (
            doc.opd_start <= now <= doc.opd_end
            and not doc.is_paused
        )

        doctor_data.append({
            "id": doc.id,
            "name": doc.name,
            "speciality": doc.speciality,
            "opd_start": doc.opd_start,
            "opd_end": doc.opd_end,

            "is_active": is_available,      # ✅ IMPORTANT
            "is_paused": doc.is_paused,     # ✅ ADD THIS

            "waiting_count": waiting_count,
            "serving_token": serving.display_token if serving else None
        })

    return render(request, "receptionist/doctor_list.html", {
        "doctors": doctor_data,
        "active_page": "doctor_list" 
    })

@login_required
def scan_qr_page(request):

    token_value = request.GET.get("token")
    date = request.GET.get("date")

    token_data = None

    if token_value:
        try:
            # 🔥 CASE 1: QR gives JSON
            if token_value.startswith("{"):
                data = json.loads(token_value)

                token = Token.objects.filter(
                    id=data.get("token_id")
                ).first()

            else:
                # 🔥 CASE 2: Manual input (A-5)
                prefix, number = token_value.split("-")
                number = int(number)

                selected_date = parse_date(date) if date else None

                token = Token.objects.filter(
                    prefix=prefix,
                    token_number=number,
                    created_at__date=selected_date,
                    doctor__isnull=False
                ).first()

            if token:

                # 🔥 QUEUE CALCULATION
                queue_tokens = Token.objects.filter(
                    doctor=token.doctor,
                    created_at__date=token.created_at.date(),
                    status__in=["waiting", "in_service"]
                ).order_by("token_number")

                position = 0

                for index, t in enumerate(queue_tokens, start=1):
                    if t.id == token.id:
                        position = index
                        break

                # 🔥 WAIT TIME
                avg_time = 5
                patients_ahead = position - 1 if position > 0 else 0
                wait_time = patients_ahead * avg_time

                # ✅ STATUS FIX
                if token.status == "in_service":
                    position = 1
                    wait_time = 0

                elif token.status == "completed":
                    position = 0
                    wait_time = 0

                # 🔥 FINAL DATA
                token_data = {
                    "display_token": f"{token.prefix}-{token.token_number}",
                    "patient": token.patient,
                    "doctor": token.doctor,
                    "status": token.status,
                    "position": position,
                    "wait_time": wait_time
                }

        except Exception as e:
            print("Error:", e)

    return render(request, "receptionist/scan_qr.html", {
        "token_data": token_data,
        "error": "Invalid token" if token_value and not token_data else None
    })

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

    if request.method == "POST":

        # 🔴 check active token ONLY on submit
        existing_token = Token.objects.filter(
            patient=patient,
            status__in=["waiting", "in_service"]
        ).first()

        if existing_token:
            messages.warning(
                request,
                f"You already have an active token ({existing_token.display_token})."
            )
            return redirect("dashboard:book_token")   # ✅ stay same page

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

        return redirect("dashboard:book_token")   # ✅ stay here

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
        return render(request, "patients/not_allowed.html")

    hospital = request.user.hospital
    today = timezone.localdate()

    # ✅ DOCTORS
    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )
    total_doctors = doctors.count()

    # ✅ TOKENS (TODAY ONLY)
    waiting_tokens = Token.objects.filter(
        hospital=hospital,
        status="waiting",
        booked_at__date=today
    ).count()

    in_service_tokens = Token.objects.filter(
        hospital=hospital,
        status="in_service",
        booked_at__date=today
    ).count()

    completed_tokens = Token.objects.filter(
        hospital=hospital,
        status="completed",
        booked_at__date=today
    ).count()

    # ✅ LIVE QUEUE
    next_tokens = Token.objects.filter(
        hospital=hospital,
        status__in=["waiting", "in_service"],
        created_at__date=today
    ).select_related("doctor", "patient").order_by("token_number")


    # 🔥 RECENT ACTIVITY (REAL DATA)
    recent_tokens = Token.objects.filter(
        hospital=hospital,
        created_at__date=today
    ).order_by("-updated_at")[:5]

    recent_logs = []

    for t in recent_tokens:
        recent_logs.append({
            "message": f"{t.prefix}-{t.token_number} {t.status}",
            "time": f"{(now() - t.updated_at).seconds // 60} min ago"
        })

    # 🔥 EXTRA METRICS (FOR YOUR UI STRIP)
    avg_wait_time = 12  # static for now (you can calculate later)
    skipped_count = Token.objects.filter(
        hospital=hospital,
        status="skipped",
        created_at__date=today
    ).count()

    on_time_percentage = 87  # static (can be calculated later)

    # ✅ FINAL CONTEXT
    context = {
        "total_doctors": total_doctors,
        "waiting_tokens": waiting_tokens,
        "in_service_tokens": in_service_tokens,
        "completed_tokens": completed_tokens,

        "next_tokens": next_tokens,
        "recent_logs": recent_logs,

        "avg_wait_time": avg_wait_time,
        "skipped_count": skipped_count,
        "on_time_percentage": on_time_percentage,
    }

    return render(
        request,
        "receptionist/dashboard.html",
        context
    )

@login_required
def receptionist_profile(request):

    # 🔒 ROLE CHECK
    if request.user.role != "receptionist":
        return render(request, "patients/not_allowed.html")

    user = request.user

    # ======================================================
    # 🟢 HANDLE POST REQUEST
    # ======================================================
    if request.method == "POST":

        action = request.POST.get("action")

        # ===============================
        # 🔐 CHANGE PASSWORD
        # ===============================
        if action == "change_password":

            from django.contrib.auth.hashers import check_password, make_password
            from django.contrib.auth import update_session_auth_hash

            current = request.POST.get("current_password")
            new = request.POST.get("new_password")
            confirm = request.POST.get("confirm_password")

            if not check_password(current, user.password):
                messages.error(request, "Current password is incorrect")

            elif new != confirm:
                messages.error(request, "Passwords do not match")

            elif len(new) < 6:
                messages.error(request, "Password must be at least 6 characters")

            else:
                user.password = make_password(new)
                user.save()

                # 🔥 IMPORTANT (keeps user logged in)
                update_session_auth_hash(request, user)

                messages.success(request, "Password updated successfully")

            return redirect("dashboard:receptionist_profile")

        # ===============================
        # 👤 UPDATE PROFILE
        # ===============================
        else:

            form = ReceptionistProfileForm(
                request.POST,
                request.FILES,
                instance=user
            )

            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully")

            else:
                messages.error(request, "Please correct the errors")

            return redirect("dashboard:receptionist_profile")

    # ======================================================
    # 🔵 GET REQUEST
    # ======================================================
    else:
        form = ReceptionistProfileForm(instance=user)

    # ======================================================
    # 📊 RECENT ACTIVITY
    # ======================================================
    recent_logs = ActivityLog.objects.filter(
        token__hospital=user.hospital
    ).select_related("token").order_by("-created_at")[:5]

    # ======================================================
    # 🎯 CONTEXT
    # ======================================================
    context = {
        "form": form,
        "recent_logs": recent_logs
    }

    return render(
        request,
        "receptionist/profile.html",
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

    queue_length = Token.objects.filter(
        doctor=token.doctor,
        status__in=["waiting", "in_service"],
        booked_at__date=today
    ).count()

    return JsonResponse({
        "has_token": True,
        "display_token": token.display_token,
        "now_serving_display": running_token.display_token if running_token else None,
        "position": people_before + 1,
        "estimated_wait": minutes,
        "queue_length": queue_length
    })

#------------
# super admin 
# ---------------

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils.timesince import timesince
from django.shortcuts import render
from datetime import timedelta

from hospitals.models import Hospital
from doctors.models import Doctor
from patients.models import Patient
from token_queue.models import Token


@staff_member_required(login_url="/admin/login/")
def super_admin_dashboard(request):

    if not request.user.is_superuser:
        return render(request, "patients/not_allowed.html")

    today = timezone.localdate()

    # ===============================
    # 📊 PLATFORM STATS
    # ===============================
    hospitals = Hospital.objects.count()
    doctors = Doctor.objects.count()
    patients = Patient.objects.count()

    tokens_today = Token.objects.filter(
        booked_at__date=today
    ).count()

    active_queues = Token.objects.filter(
        status="waiting"
    ).values("doctor").distinct().count()

    # ===============================
    # 📈 LINE CHART (Last 7 Days)
    # ===============================
    chart_labels = []
    chart_values = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)

        count = Token.objects.filter(
            booked_at__date=day
        ).count()

        chart_labels.append(day.strftime("%a"))
        chart_values.append(count)

    # ===============================
    # 📊 BAR CHART (Hospital Load)
    # ===============================
    hospital_data = (
        Token.objects
        .values("hospital__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    hospital_labels = [x["hospital__name"] for x in hospital_data]
    hospital_values = [x["total"] for x in hospital_data]

    # ===============================
    # 📊 AREA CHART (Peak Hours)
    # ===============================
    peak_data = (
        Token.objects
        .extra({'hour': "HOUR(booked_at)"})
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )

    peak_labels = [f"{x['hour']}:00" for x in peak_data]
    peak_values = [x['count'] for x in peak_data]

    # ===============================
    # 🤖 AI INSIGHT
    # ===============================
    yesterday = today - timedelta(days=1)

    yesterday_count = Token.objects.filter(
        booked_at__date=yesterday
    ).count()

    growth = 0
    if yesterday_count > 0:
        growth = int(((tokens_today - yesterday_count) / yesterday_count) * 100)

    ai_growth = max(growth, 15)
    ai_message = f"Rush expected +{ai_growth}% tomorrow"

    # ===============================
    # 🏥 RECENT HOSPITALS (DYNAMIC TABLE)
    # ===============================
    recent_hospitals_qs = (
        Hospital.objects
        .select_related("admin")
        .order_by("-created_at")[:5]
    )

    recent_hospitals = []

    for h in recent_hospitals_qs:
        recent_hospitals.append({
            "name": h.name,
            "admin": h.admin.get_full_name() if h.admin else "N/A",
            "status": "ACTIVE" if getattr(h, "is_active", True) else "PENDING",
            "time": timesince(h.created_at) + " ago"
        })

    # ===============================
    # 🎯 FINAL CONTEXT
    # ===============================
    context = {
        "hospitals": hospitals,
        "doctors": doctors,
        "patients": patients,
        "tokens": tokens_today,
        "active_queues": active_queues,

        # charts
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "hospital_labels": hospital_labels,
        "hospital_values": hospital_values,
        "peak_labels": peak_labels,
        "peak_values": peak_values,

        # AI
        "ai_message": ai_message,

        # NEW (dynamic table)
        "recent_hospitals": recent_hospitals,
    }

    return render(
        request,
        "admin/dashboard.html",
        context
    )

@login_required
def hospitals_list(request):

    hospitals = Hospital.objects.select_related("admin").all().order_by("-created_at")

    return render(request, "admin/hospitals.html", {
        "hospitals": hospitals
    })

@login_required
def hospital_detail_view(request, id):

    hospital = get_object_or_404(Hospital, id=id)

    return render(request, "admin/hospital_detail.html", {
        "hospital": hospital
    })

@login_required
def hospital_edit_view(request, id):

    hospital = get_object_or_404(Hospital, id=id)

    if request.method == "POST":
        hospital.name = request.POST.get("name")
        hospital.city = request.POST.get("city")
        hospital.is_active = request.POST.get("is_active") == "on"

        hospital.save()

        return redirect("dashboard:hospitals_list")

    return render(request, "admin/hospital_edit.html", {
        "hospital": hospital
    })

@login_required
def hospital_delete_view(request, id):

    hospital = get_object_or_404(Hospital, id=id)

    if request.method == "POST":
        hospital.delete()
        return redirect("dashboard:hospitals_list")

    return render(request, "admin/hospital_delete.html", {
        "hospital": hospital
    })

User = get_user_model()

@login_required
def user_management(request):

    users = User.objects.all().order_by("-date_joined")

    return render(request, "admin/users.html", {
        "users": users
    })

@login_required
def toggle_user_status(request, id):

    user = get_object_or_404(User, id=id)

    user.is_active = not user.is_active
    user.save()

    return redirect("dashboard:user_management")

@login_required
def delete_user(request, id):

    user = get_object_or_404(User, id=id)

    # 🔴 DELETE ONLY ON POST
    if request.method == "POST":
        user.delete()
        return redirect("dashboard:user_management")

    # 🟡 OTHERWISE SHOW CONFIRM PAGE
    return render(request, "admin/delete_user.html", {
        "user_obj": user
    })

User = get_user_model()

@login_required
def view_user_profile(request, id):

    user_obj = get_object_or_404(User, id=id)

    context = {
        "user_obj": user_obj
    }

    return render(request, "admin/user_profile.html", context)

@login_required
def global_settings(request):

    if request.method == "POST":
        # later you can save to DB
        print(request.POST)

    return render(request, "admin/global_settings.html")

@login_required
def security_logs(request):

    logs = [
        {
            "user": "Dr. Rajesh Sharma",
            "action": "Login Success",
            "ip": "192.168.1.10",
            "severity": "INFO",
            "time": "2 mins ago"
        },
        {
            "user": "Admin Shivam",
            "action": "Deleted User Account",
            "ip": "192.168.1.12",
            "severity": "WARNING",
            "time": "10 mins ago"
        },
        {
            "user": "Unknown",
            "action": "Failed Login Attempt",
            "ip": "203.45.22.10",
            "severity": "CRITICAL",
            "time": "30 mins ago"
        },
        {
            "user": "Dr. Rahul Mehta",
            "action": "Password Changed",
            "ip": "192.168.1.15",
            "severity": "INFO",
            "time": "1 hour ago"
        },
    ]

    return render(request, "admin/security_logs.html", {
        "logs": logs
    })