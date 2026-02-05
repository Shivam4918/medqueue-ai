from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.permissions import IsHospitalAdmin
from django.core.exceptions import PermissionDenied
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from datetime import datetime
from hospitals.models import Hospital
from doctors.models import Doctor

from .reports_export import fetch_events, export_csv, export_pdf


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

@login_required
def export_reports(request):
    user = request.user

    if not user.is_superuser and user.role != "hospital_admin":
        raise PermissionDenied

    try:
        doctor = Doctor.objects.get(user=request.user)
        hospital = doctor.hospital
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found", status=403)
    except Hospital.DoesNotExist:
        return HttpResponse("Hospital not found", status=403)


    start = parse_date(request.GET.get("start"))
    end = parse_date(request.GET.get("end"))
    doctor_id = request.GET.get("doctor")
    fmt = request.GET.get("format", "csv")

    if not start or not end:
        return HttpResponse("Invalid date range", status=400)

    events = fetch_events(
        hospital_id=hospital.id,
        start_date=datetime.combine(start, datetime.min.time()),
        end_date=datetime.combine(end, datetime.max.time()),
        doctor_id=int(doctor_id) if doctor_id else None,
    )

    if fmt == "pdf":
        return export_pdf(events, "OPD Analytics Report")

    return export_csv(events, "opd_report")

