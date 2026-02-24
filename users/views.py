from datetime import timedelta
import random, re
from django.conf import settings
from email.mime.image import MIMEImage
import os
import time
from .models import User
from patients.models import Patient
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import OTP, User, Notification, generate_otp
from django.contrib.messages import get_messages
from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .portal import PORTAL_ROLE_MAP
from .utils import redirect_user_dashboard

from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from .models import EmailOTP
from django.contrib.auth.hashers import make_password

from django.views.decorators.http import require_GET



# =========================================================
# OTP AUTHENTICATION (API / MOBILE / FUTURE)
# =========================================================

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        try:
            otp_code = generate_otp()
        except Exception:
            otp_code = str(random.randint(100000, 999999))

        OTP.objects.create(phone=phone, otp=otp_code)

        try:
            send_mail(
                subject="Your MedQueue AI OTP",
                message=f"Your login OTP is: {otp_code}",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@medqueue.ai")],
                fail_silently=True,
            )
        except Exception:
            pass

        # Dev visibility
        print("\n======== OTP SENT ========")
        print(f"Phone: {phone}")
        print(f"OTP:   {otp_code}")
        print("===========================\n")

        return Response(
            {"message": "OTP sent successfully"},
            status=status.HTTP_200_OK
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_obj = serializer.validated_data.get("otp_obj")
        phone = serializer.validated_data.get("phone")
        otp_value = serializer.validated_data.get("otp")

        if not otp_obj:
            try:
                otp_obj = OTP.objects.filter(phone=phone).latest("created_at")
            except OTP.DoesNotExist:
                return Response({"error": "OTP not found"}, status=404)

        if timezone.now() > otp_obj.created_at + timedelta(minutes=5):
            return Response({"error": "OTP expired"}, status=400)

        if otp_obj.is_used:
            return Response({"error": "OTP already used"}, status=400)

        if str(otp_value) != str(otp_obj.otp):
            return Response({"error": "Invalid OTP"}, status=400)

        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used"])

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"username": phone}
        )

        return Response(
            {
                "message": "OTP verified successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "phone": user.phone,
                },
                "created": created,
            },
            status=200
        )


# =========================================================
# WEB PORTAL LOGIN (USERNAME / PASSWORD)
# =========================================================

def portal_login(request, portal):
    """
    Handles login for:
    /auth/patient/login/
    /auth/doctor/login/
    /auth/receptionist/login/
    /auth/hospital/login/
    """

    expected_role = PORTAL_ROLE_MAP.get(portal)
    if not expected_role:
        return redirect("/")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid username or password")
            return render(request, "auth/login.html", {"role": portal})

        # Block superuser from portals
        if user.is_superuser:
            messages.error(request, "Please use admin login")
            return redirect("/admin/login/")

        # Role protection
        if user.role != expected_role:
            logout(request)
            messages.error(request, "Unauthorized portal access")
            return render(request, "auth/login.html", {"role": portal})

        login(request, user)

        messages.success(
            request,
            f"Welcome {user.username}! Logged in as {user.role.replace('_', ' ').title()}"
        )

        return redirect_user_dashboard(user)

    return render(
        request,
        "auth/login.html",
        {
            "role": portal,
            "portal_brand": {
                "patient": "🧍 Patient Portal",
                "doctor": "👨‍⚕️ Doctor Portal",
                "receptionist": "🧾 Reception Desk",
                "hospital": "🏥 Hospital Admin",
            }.get(portal, "MedQueue Login")
        }
    )

# ======================
# Patient Register (WEB)
# ======================

def patient_register(request):
    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # ==============================
        # 1️⃣ FULL NAME VALIDATION
        # ==============================
        if not re.fullmatch(r"[A-Za-z ]{3,100}", name):
            messages.error(request, "Full name must contain only alphabets and spaces (3-100 characters).")
            return redirect("users:patient_register")

        # ==============================
        # 2️⃣ PHONE VALIDATION (INDIA)
        # ==============================
        if not re.fullmatch(r"[6-9]\d{9}", phone):
            messages.error(request, "Enter a valid 10-digit Indian phone number.")
            return redirect("users:patient_register")

        # ==============================
        # 3️⃣ EMAIL VALIDATION
        # ==============================
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Enter a valid email address.")
            return redirect("users:patient_register")

        # ==============================
        # 4️⃣ PASSWORD VALIDATION
        # ==============================
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("users:patient_register")

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return redirect("users:patient_register")

        if not re.search(r"[A-Z]", password1):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect("users:patient_register")

        if not re.search(r"[a-z]", password1):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect("users:patient_register")

        if not re.search(r"\d", password1):
            messages.error(request, "Password must contain at least one number.")
            return redirect("users:patient_register")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password1):
            messages.error(request, "Password must contain at least one special character.")
            return redirect("users:patient_register")

        if name.lower() in password1.lower() or phone in password1:
            messages.error(request, "Password cannot be similar to name or phone.")
            return redirect("users:patient_register")

        # ==============================
        # 5️⃣ DUPLICATE CHECK
        # ==============================
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("users:patient_register")

        if User.objects.filter(phone=phone).exists():
            messages.error(request, "Phone number already registered.")
            return redirect("users:patient_register")

        # ==============================
        # STORE REGISTRATION DATA IN SESSION
        # ==============================

        otp = get_random_string(6, allowed_chars="0123456789")

        request.session["registration_data"] = {
            "name": name,
            "phone": phone,
            "email": email,
            "password": make_password(password1),
            "otp": otp,
            "otp_created": time.time()
        }

        # ==============================
        # SEND PROFESSIONAL OTP EMAIL
        # ==============================

        subject = "Verify Your Email | MedQueue AI"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [email]

        html_content = render_to_string(
            "emails/verify_email.html",
            {
                "name": name,
                "otp": otp
            }
        )

        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            to
        )

        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        storage = get_messages(request)
        for _ in storage:
            pass

        return redirect("users:verify_email_otp")

    return render(request, "users/patient_register.html")

def check_user_exists(request):
    email = request.GET.get("email")
    phone = request.GET.get("phone")

    response = {
        "email_exists": False,
        "phone_exists": False
    }

    if email:
        response["email_exists"] = User.objects.filter(email=email.lower()).exists()

    if phone:
        response["phone_exists"] = User.objects.filter(phone=phone).exists()

    return JsonResponse(response)

def verify_email_otp(request):

    registration_data = request.session.get("registration_data")

    if not registration_data:
        messages.error(request, "Session expired. Please register again.")
        return redirect("users:patient_register")

    otp_created = registration_data.get("otp_created", 0)
    expiry_seconds = 120
    remaining_time = int(expiry_seconds - (time.time() - otp_created))

    # If expired before POST
    if remaining_time <= 0:
        remaining_time = 0

    if request.method == "POST":

        entered_otp = request.POST.get("otp", "").strip()

        if not entered_otp:
            messages.error(request, "Please enter the OTP.")
            return render(request, "users/verify_otp.html", {
                "remaining_time": remaining_time
            })

        if remaining_time <= 0:
            messages.error(request, "OTP expired. Please resend OTP.")
            return render(request, "users/verify_otp.html", {
                "remaining_time": 0
            })

        if entered_otp != registration_data["otp"]:
            messages.error(request, "Invalid OTP.")
            return render(request, "users/verify_otp.html", {
                "remaining_time": remaining_time
            })

        # SUCCESS
        user = User.objects.create(
            username=registration_data["email"],
            email=registration_data["email"],
            phone=registration_data["phone"],
            first_name=registration_data["name"],
            role="patient",
            is_active=True,
            password=registration_data["password"],
        )

        Patient.objects.create(
            user=user,
            name=registration_data["name"],
            phone=registration_data["phone"]
        )

        del request.session["registration_data"]

        login(request, user)
        return render(request, "users/success.html")

    return render(request, "users/verify_otp.html", {
        "remaining_time": remaining_time
    })


@require_GET
def resend_otp(request):

    registration_data = request.session.get("registration_data")

    if not registration_data:
        return redirect("users:patient_register")

    otp = get_random_string(6, allowed_chars="0123456789")

    registration_data["otp"] = otp
    registration_data["otp_created"] = time.time()

    request.session["registration_data"] = registration_data

    # ✅ IMPORTANT: pass name explicitly
    html_content = render_to_string(
        "emails/verify_email.html",
        {
            "name": registration_data["name"],
            "otp": otp
        }
    )

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject="Verify Your Email | MedQueue AI",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[registration_data["email"]],
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

    return redirect("users:verify_email_otp")

# =========================================================
# NOTIFICATIONS
# =========================================================

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(
        request,
        "notifications/list.html",
        {"notifications": notifications}
    )


@login_required
def mark_notifications_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    return redirect("notifications")

