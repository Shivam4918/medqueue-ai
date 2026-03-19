#hospitals/views.py

from rest_framework import viewsets
from .models import Hospital
from .serializers import HospitalSerializer
from .permissions import IsHospitalAdminOrReadOnly
from django.db.models.functions import ExtractHour
from django.db.models import Count, Avg, F
from doctors.models import Doctor
from token_queue.models import Token
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from notifications.email_service import send_hospital_admin_welcome_email
from notifications.email_service import send_doctor_welcome_email
from notifications.email_service import send_receptionist_welcome_email
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
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

User = get_user_model()


def create_hospital(request):

    if request.method == "POST":

        hospital_name = request.POST.get("hospital_name")
        city = request.POST.get("city")
        address = request.POST.get("address")
        contact_phone = request.POST.get("contact_phone")

        admin_email = request.POST.get("admin_email")
        admin_password = request.POST.get("admin_password")
        admin_name = request.POST.get("admin_name")

        # create hospital admin user
        admin_user = User.objects.create_user(
            username=admin_email,
            email=admin_email,
            password=admin_password,
            first_name=admin_name,
            role="hospital_admin"
        )

        # create hospital
        hospital = Hospital.objects.create(
            name=hospital_name,
            city=city,
            address=address,
            contact_phone=contact_phone,
            admin=admin_user
        )

        # Send email
        send_hospital_admin_welcome_email(
            admin_name,
            admin_email,
            hospital.name,
            admin_password
        )

        return redirect("/admin/dashboard/")

    return render(request, "hospitals/create_hospital.html")

@login_required
def hospital_dashboard(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    if not hospital:
        return render(request, "patients/not_allowed.html")

    # Doctors in this hospital
    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )

    total_doctors = doctors.count()

    # Queue stats
    waiting_tokens = Token.objects.filter(
        hospital=hospital,
        status="waiting"
    ).count()

    in_service_tokens = Token.objects.filter(
        hospital=hospital,
        status="in_service"
    ).count()

    today = timezone.now().date()

    completed_tokens = Token.objects.filter(
        hospital=hospital,
        status="completed",
        updated_at__date=today
    ).count()

    context = {
        "hospital": hospital,
        "doctors": doctors,
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
def hospital_doctors(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )

    context = {
        "hospital": hospital,
        "doctors": doctors
    }

    return render(
        request,
        "hospitals/doctors_list.html",
        context
    )

@login_required
def add_doctor(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        speciality = request.POST.get("speciality")
        opd_start = request.POST.get("opd_start")
        opd_end = request.POST.get("opd_end")

        # Create doctor user
        doctor_user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
            role="doctor"
        )

        # Create doctor profile
        Doctor.objects.create(
            user=doctor_user,
            hospital=hospital,
            name=name,
            speciality=speciality,
            opd_start=opd_start,
            opd_end=opd_end
        )

        send_doctor_welcome_email(
            name,
            email,
            hospital.name,
            password
        )
        
        send_doctor_welcome_email(
            name,
            email,
            hospital.name,
            password
        )

        return redirect("hospital_doctors")

    return render(request, "hospitals/add_doctor.html")

@login_required
def edit_doctor(request, doctor_id):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    doctor = get_object_or_404(
        Doctor,
        id=doctor_id,
        hospital=hospital
    )

    if request.method == "POST":

        doctor.name = request.POST.get("name")
        doctor.speciality = request.POST.get("speciality")
        doctor.opd_start = request.POST.get("opd_start")
        doctor.opd_end = request.POST.get("opd_end")

        doctor.save()

        return redirect("hospital_doctors")

    context = {
        "doctor": doctor
    }

    return render(
        request,
        "hospitals/edit_doctor.html",
        context
    )

@login_required
def disable_doctor(request, doctor_id):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    doctor = get_object_or_404(
        Doctor,
        id=doctor_id,
        hospital=hospital
    )

    doctor.is_active = False
    doctor.save()

    return redirect("hospital_doctors")

@login_required
def hospital_staff(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    receptionists = User.objects.filter(
        role="receptionist",
        hospital=hospital,
        is_active=True
    )

    context = {
        "hospital": hospital,
        "receptionists": receptionists
    }

    return render(
        request,
        "hospitals/staff_list.html",
        context
    )

@login_required
def add_receptionist(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
            role="receptionist",
            hospital=hospital
        )

        send_receptionist_welcome_email(
            name,
            email,
            hospital.name,
            password
        )

        return redirect("hospital_staff")

    return render(request, "hospitals/add_receptionist.html")

@login_required
def disable_receptionist(request, user_id):

    hospital = Hospital.objects.filter(admin=request.user).first()

    receptionist = get_object_or_404(
        User,
        id=user_id,
        role="receptionist",
        hospital=hospital
    )

    receptionist.is_active = False
    receptionist.save()

    return redirect("hospital_staff")

@login_required
def hospital_queue_monitor(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    if not hospital:
        return render(request, "patients/not_allowed.html")

    doctors = Doctor.objects.filter(
        hospital=hospital,
        is_active=True
    )

    queue_data = []

    for doctor in doctors:

        now_serving = Token.objects.filter(
            doctor=doctor,
            status="in_service"
        ).order_by("token_number").first()

        waiting_tokens = Token.objects.filter(
            doctor=doctor,
            status="waiting"
        ).order_by("priority", "token_number")

        next_tokens = waiting_tokens[:5]

        queue_data.append({
            "doctor": doctor,
            "now_serving": now_serving,
            "waiting_count": waiting_tokens.count(),
            "next_tokens": next_tokens
        })

    context = {
        "hospital": hospital,
        "queue_data": queue_data
    }

    return render(
        request,
        "hospitals/queue_monitor.html",
        context
    )

from django.utils import timezone
from django.db.models import Count, Avg, F
from token_queue.models import Token
from doctors.models import Doctor


@login_required
def hospital_analytics(request):

    if request.user.role != "hospital_admin":
        return render(request, "patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    today = timezone.localdate()

    tokens_today = Token.objects.filter(
        hospital=hospital,
        booked_at__date=today
    )

    total_tokens = tokens_today.count()

    completed = tokens_today.filter(status="completed").count()

    waiting = tokens_today.filter(status="waiting").count()

    in_service = tokens_today.filter(status="in_service").count()

    skipped = tokens_today.filter(status="skipped").count()

    # =============================
    # Average Waiting Time
    # =============================

    avg_wait = (
        tokens_today
        .exclude(called_at=None)
        .annotate(wait_time=F("called_at") - F("booked_at"))
        .aggregate(avg=Avg("wait_time"))
    )

    avg_wait_minutes = 0

    if avg_wait["avg"]:
        avg_wait_minutes = int(avg_wait["avg"].total_seconds() / 60)

    # =============================
    # Doctor Performance
    # =============================

    doctor_stats = (
        Token.objects
        .filter(hospital=hospital)
        .values("doctor__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    doctor_labels = [d["doctor__name"] for d in doctor_stats]
    doctor_values = [d["total"] for d in doctor_stats]

    # =============================
    # Hourly Patient Load
    # =============================

    hourly_data = (
        Token.objects.filter(
            hospital=hospital,
            booked_at__date=today
        )
        .annotate(hour=ExtractHour("booked_at"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )

    hour_labels = [h["hour"] for h in hourly_data]
    hour_values = [h["count"] for h in hourly_data]

    # =============================
    # Peak Hour
    # =============================

    peak_hour = None

    if hourly_data:
        peak = max(hourly_data, key=lambda x: x["count"])
        peak_hour = peak["hour"]

    context = {

        "hospital": hospital,

        "total_tokens": total_tokens,
        "completed": completed,
        "waiting": waiting,
        "in_service": in_service,
        "skipped": skipped,

        "avg_wait": avg_wait_minutes,
        "peak_hour": peak_hour,

        "doctor_labels": doctor_labels,
        "doctor_values": doctor_values,

        "hour_labels": hour_labels,
        "hour_values": hour_values,

        "doctor_stats": doctor_stats
    }

    return render(
        request,
        "hospitals/analytics.html",
        context
    )

@login_required
def hospital_profile(request):

    if request.user.role != "hospital_admin":
        return render(request,"patients/not_allowed.html")

    hospital = Hospital.objects.filter(admin=request.user).first()

    if request.method == "POST":

        action = request.POST.get("action")

        # -------------------------
        # UPDATE PROFILE
        # -------------------------
        if action == "update_profile":

            name = request.POST.get("name")

            if name:
                request.user.first_name = name
                request.user.save()

            if request.FILES.get("avatar"):
                hospital.profile_picture = request.FILES["avatar"]
                hospital.save()

            messages.success(request, "Profile updated successfully")


        # -------------------------
        # CHANGE PASSWORD
        # -------------------------
        elif action == "change_password":

            current = request.POST.get("current_password")
            new = request.POST.get("new_password")
            confirm = request.POST.get("confirm_password")

            if not check_password(current, request.user.password):

                messages.error(request, "Current password incorrect")
                return redirect("hospital_profile")

            elif new != confirm:

                messages.error(request, "Passwords do not match")
                return redirect("hospital_profile")

            elif len(new) < 8:

                messages.error(request, "Password must be at least 8 characters")
                return redirect("hospital_profile")

            else:

                request.user.set_password(new)
                request.user.save()

                messages.success(request, "Password updated successfully")

                # keep user logged in after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)

                return redirect("hospital_profile")


        # -------------------------
        # UPDATE HOSPITAL SETTINGS
        # -------------------------
        elif action == "hospital_settings":

            hospital.token_limit = request.POST.get("token_limit")
            hospital.opd_start = request.POST.get("opd_start")
            hospital.opd_end = request.POST.get("opd_end")

            hospital.save()

            messages.success(request,"Hospital settings updated")


        return redirect("hospital_profile")


    context = {
        "hospital": hospital
    }

    return render(
        request,
        "hospitals/profile.html",
        context
    )