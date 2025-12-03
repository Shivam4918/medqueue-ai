# dashboard/views.py
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
