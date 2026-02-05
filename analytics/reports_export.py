import pandas as pd
from io import BytesIO
from datetime import datetime

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .mongo_client import get_events_collection
from .events import (
    TOKEN_CREATED,
    TOKEN_COMPLETED,
    TOKEN_SKIPPED,
)

def fetch_events(hospital_id, start_date, end_date, doctor_id=None):
    query = {
        "hospital_id": hospital_id,
        "timestamp": {"$gte": start_date, "$lte": end_date},
        "event": {"$in": [TOKEN_CREATED, TOKEN_COMPLETED, TOKEN_SKIPPED]},
    }

    if doctor_id:
        query["doctor_id"] = doctor_id

    return list(get_events_collection().find(query))

def export_csv(events, filename):
    if not events:
        return HttpResponse("No data", status=204)

    df = pd.DataFrame(events)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

    df.to_csv(response, index=False)
    return response

def export_pdf(events, title):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 40, title)

    y = height - 80
    p.setFont("Helvetica", 10)

    for event in events:
        line = (
            f"{event['event']} | "
            f"Doctor: {event.get('doctor_id')} | "
            f"Token: {event.get('token_id')} | "
            f"{event['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        )
        p.drawString(40, y, line)
        y -= 15

        if y < 50:
            p.showPage()
            y = height - 40

    p.save()
    buffer.seek(0)

    return HttpResponse(
        buffer,
        content_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="report.pdf"'
        },
    )
