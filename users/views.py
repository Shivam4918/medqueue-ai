from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.contrib.auth.hashers import make_password

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

    expected_role = PORTAL_ROLE_MAP.get(portal)
    if not expected_role:
        return redirect("/")

    if request.method == "POST":
        email = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if not user:
            messages.error(request, "Invalid email or password.")
            return render(request, "auth/login.html", {"role": portal})

        if not user.is_active:
            messages.error(request, "Please verify your email first.")
            return render(request, "auth/login.html", {"role": portal})

        if user.role != expected_role:
            logout(request)
            messages.error(request, "Unauthorized access.")
            return render(request, "auth/login.html", {"role": portal})

        login(request, user)
        return redirect_user_dashboard(user)

    return render(request, "auth/login.html", {"role": portal})

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

def password_reset_request(request):

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()

        user = User.objects.filter(email=email, role="patient").first()

        if user:
            token_generator = PasswordResetTokenGenerator()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)

            reset_link = request.build_absolute_uri(
                reverse("users:password_reset_confirm",
                        kwargs={"uidb64": uid, "token": token})
            )

            RESET_EXPIRY_MINUTES = 15  # You can change anytime
            request.session["reset_link_created_at"] = int(time.time())
            
            html_content = render_to_string(
                "emails/password_reset_email.html",
                {
                    "name": user.first_name,
                    "reset_link": reset_link,
                    "expiry_minutes": RESET_EXPIRY_MINUTES,
                }
            )

            email_message = EmailMultiAlternatives(
                "Reset Your Password | MedQueue AI",
                strip_tags(html_content),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )

            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

        # Save cooldown timestamp
        request.session["reset_requested_at"] = int(time.time())

        return redirect("users:password_reset_done")

    return render(request, "auth/password_reset_request.html")

def password_reset_confirm(request, uidb64, token):

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()

    if user is None or not token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired reset link.")
        return redirect("users:patient_login")

    # Use same timeout as settings
    RESET_EXPIRY_SECONDS = 900  # Must match settings.py
    created_at = request.session.get("reset_link_created_at")

    if created_at:
        elapsed = int(time.time()) - created_at
        remaining_time = RESET_EXPIRY_SECONDS - elapsed
    else:            
        remaining_time = 0

    if remaining_time < 0:
       remaining_time = 0

    if request.method == "POST":

        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "auth/password_reset_confirm.html", {
                "remaining_time": remaining_time
            })

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "auth/password_reset_confirm.html", {
                "remaining_time": remaining_time
            })

        if not re.search(r"[A-Z]", password1):
            messages.error(request, "Password must contain an uppercase letter.")
            return render(request, "auth/password_reset_confirm.html", {
                "remaining_time": remaining_time
            })

        if not re.search(r"[a-z]", password1):
            messages.error(request, "Password must contain a lowercase letter.")
            return render(request, "auth/password_reset_confirm.html", {
                "remaining_time": remaining_time
            })

        if not re.search(r"\d", password1):
            messages.error(request, "Password must contain a number.")
            return render(request, "auth/password_reset_confirm.html", {
                "remaining_time": remaining_time
            })

        if not re.search(r"[!@#$%^&*]", password1):
            messages.error(request, "Password must contain a special character.")
            return render(request, "auth/password_reset_confirm.html", {
                "remaining_time": remaining_time
            })

        user.password = make_password(password1)
        user.save()

        return render(request, "auth/password_reset_success.html")

    return render(request, "auth/password_reset_confirm.html", {
        "remaining_time": remaining_time
    })

def password_reset_done(request):

    requested_at = request.session.get("reset_requested_at")
    cooldown = 60

    remaining = 0
    if requested_at:
        remaining = cooldown - (int(time.time()) - requested_at)
        if remaining < 0:
            remaining = 0

    return render(
        request,
        "auth/password_reset_done.html",
        {"remaining_time": remaining}
    )

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

