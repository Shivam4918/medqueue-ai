# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from hospitals.models import Hospital
from doctors.models import Doctor


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
    """
    Simple patient page showing current token (uses JS fetch to call API).
    URL example: /dashboard/patient/
    """
    return render(request, "dashboard/patient_token.html", {})


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
