from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.permissions import IsHospitalAdmin
from django.core.exceptions import PermissionDenied

from .reports import (
    total_patients_today,
    average_wait_time_minutes,
    peak_opd_hours,
    tokens_per_doctor,
    no_show_rate,
)
from doctors.models import Doctor


@login_required
def hospital_admin_dashboard(request):
    user = request.user

    # 🔐 Restrict access
    if not user.is_superuser and user.role != "hospital_admin":
        raise PermissionDenied("Only hospital admins allowed")

    hospital = getattr(user, "hospital", None)
    if hospital is None:
        raise PermissionDenied("Hospital not assigned")

    hospital_id = hospital.id

    # 📊 KPI Metrics
    context = {
        "total_patients": total_patients_today(hospital_id),
        "avg_wait": average_wait_time_minutes(hospital_id),
        "no_show_rate": no_show_rate(hospital_id),
    }

    # ⏰ Peak OPD Hour
    peak_hours = peak_opd_hours(hospital_id)
    context["peak_hour"] = peak_hours[0]["_id"] if peak_hours else "N/A"

    # 👨‍⚕️ Doctor-wise stats
    doctor_stats = tokens_per_doctor(hospital_id)
    doctor_map = {
        d.id: d.name for d in Doctor.objects.filter(hospital=hospital)
    }

    context["doctor_stats"] = [
        {
            "doctor": doctor_map.get(d["_id"], "Unknown"),
            "total": d["total_tokens"],
        }
        for d in doctor_stats
    ]

    # 📈 Chart data
    context["chart_labels"] = [str(h["_id"]) for h in peak_hours]
    context["chart_values"] = [h["count"] for h in peak_hours]

    return render(
        request,
        "hospitals/admin_dashboard.html",
        context
    )
