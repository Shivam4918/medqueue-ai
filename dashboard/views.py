# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from hospitals.models import Hospital
from doctors.models import Doctor

from token_queue.models import Token
from token_queue.services import estimate_wait_for_token
from patients.services import get_or_create_patient_from_user

from analytics.reports import (
    total_patients_today,
    tokens_per_doctor,
    peak_opd_hours,
    average_wait_time_minutes,
    no_show_rate,
)

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Allow only staff users (is_staff or is_superuser).
    You can change to role-based check (user.role == 'hospital_admin') if desired.
    """
    def test_func(self):
        user = self.request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))

    def handle_no_permission(self):
        # fallback to default behaviour (redirect to login)
        return super().handle_no_permission()


class DashboardHomeView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = "dashboard/hospital_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hospitals"] = Hospital.objects.all().order_by("name")
        return ctx


class HospitalDetailView(LoginRequiredMixin, StaffRequiredMixin, DetailView):
    model = Hospital
    template_name = "dashboard/hospital_detail.html"
    context_object_name = "hospital"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # list doctors belonging to this hospital
        ctx["doctors"] = Doctor.objects.filter(hospital_id=self.object.id).order_by("user__username")
        return ctx


# ---------------------------
# Simple frontend pages (Week3 / Week6)
# ---------------------------

@login_required
def patient_token_page(request):
    if getattr(request.user, "role", None) != "patient":
        return render(request, "patients/not_allowed.html")

    patient = get_or_create_patient_from_user(request.user)

    token = Token.objects.filter(
        patient=patient,
        status__in=["waiting", "in_service"]
    ).select_related("doctor", "hospital").first()

    context = {"has_token": False}

    if token:
        minutes, eta_dt = estimate_wait_for_token(
            token.doctor.id,
            token.token_number
        )

        context.update({
            "has_token": True,
            "active_token": token,
            "token_number": token.token_number,
            "doctor_name": token.doctor.name,
            "hospital_name": token.hospital.name,
            "status": token.status.replace("_", " ").title(),
            "estimated_wait": minutes,
            "eta": timezone.localtime(eta_dt),
        })

    return render(request, "patients/home.html", context)


@login_required
def doctor_queue_page(request):
    """
    Doctor queue dashboard. Provide doctor_id in context when the logged-in user
    has an attached doctor_profile so the template can read it easily.
    """
    # optional role check:
    # if getattr(request.user, "role", None) != "doctor" and not request.user.is_superuser:
    #     return redirect("dashboard:login")

    doctor_id = None
    try:
        doctor_profile = getattr(request.user, "doctor_profile", None)
        if doctor_profile:
            doctor_id = getattr(doctor_profile, "id", None)
    except Exception:
        doctor_id = None

    return render(request, "dashboard/doctor_queue.html", {"doctor_id": doctor_id})

@login_required
def receptionist_walkin_page(request):
    """
    Walk-in form for receptionists.
    Access control: only users with role 'receptionist' (or superusers) are allowed.
    Redirects other authenticated users to patient page.
    """
    if getattr(request.user, "role", None) != "receptionist" and not request.user.is_superuser:
        return redirect("dashboard:patient-token")
    return render(request, "dashboard/receptionist_walkin.html", {})

@login_required
def receptionist_queue_page(request):
    if getattr(request.user, "role", None) != "receptionist" and not request.user.is_superuser:
        return redirect("dashboard:patient-token")

    doctors = Doctor.objects.all().order_by("user__username")

    return render(
        request,
        "dashboard/receptionist_queue.html",
        {"doctors": doctors}
    )


@login_required
def doctor_dashboard(request):
    """
    Doctor dashboard with live queue (Step 7).
    Only users with doctor profile can access.
    """
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect("dashboard:home")  # or patient page

    return render(
        request,
        "dashboard/doctor_dashboard.html",
        {"doctor": doctor}
    )

@login_required
def hospital_analytics_dashboard(request, hospital_id):
    # 🔒 Access control
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect("dashboard:login")

    # MongoDB analytics
    total_patients = total_patients_today(hospital_id)
    avg_wait = average_wait_time_minutes(hospital_id)
    peak_hours = peak_opd_hours(hospital_id)
    no_show = no_show_rate(hospital_id)
    doctor_tokens = tokens_per_doctor(hospital_id)

    # Prepare chart data
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

    return render(
        request,
        "hospitals/admin_dashboard.html",
        context
    )

