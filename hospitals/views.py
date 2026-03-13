from rest_framework import viewsets
from .models import Hospital
from .serializers import HospitalSerializer
from .permissions import IsHospitalAdminOrReadOnly

from doctors.models import Doctor
from token_queue.models import Token

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from notifications.email_service import send_hospital_admin_welcome_email
from notifications.email_service import send_doctor_welcome_email
from notifications.email_service import send_receptionist_welcome_email
from django.contrib.auth.decorators import login_required

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

    completed_tokens = Token.objects.filter(
        hospital=hospital,
        status="completed"
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