from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_hospital_admin_welcome_email(admin_name, admin_email, hospital_name, password):

    subject = "Welcome to MedQueue AI – Hospital Admin Account Created"

    login_url = "http://127.0.0.1:8000/hospital-admin/login/"

    context = {
        "admin_name": admin_name,
        "hospital_name": hospital_name,
        "email": admin_email,
        "password": password,
        "login_url": login_url,
    }

    html_content = render_to_string(
        "emails/hospital_welcome.html",
        context
    )

    email = EmailMultiAlternatives(
        subject,
        "",
        settings.DEFAULT_FROM_EMAIL,
        [admin_email]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

def send_doctor_welcome_email(
    doctor_name,
    doctor_email,
    hospital_name,
    password
):

    from django.conf import settings
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags

    subject = "Doctor Account Created | MedQueue AI"

    html_content = render_to_string(
        "emails/doctor_welcome.html",
        {
            "doctor_name": doctor_name,
            "hospital_name": hospital_name,
            "email": doctor_email,
            "password": password,
            "login_url": "http://127.0.0.1:8000/doctor/login/"
        }
    )

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [doctor_email]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

def send_receptionist_welcome_email(
    name,
    email,
    hospital_name,
    password
):

    from django.conf import settings
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags

    subject = "Receptionist Account Created | MedQueue AI"

    html_content = render_to_string(
        "emails/receptionist_welcome.html",
        {
            "name": name,
            "hospital_name": hospital_name,
            "email": email,
            "password": password,
            "login_url": "http://127.0.0.1:8000/receptionist/login/"
        }
    )

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )

    email.attach_alternative(html_content, "text/html")
    email.send()