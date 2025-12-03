# users/views.py
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import OTP, User, generate_otp
from .serializers import SendOTPSerializer, VerifyOTPSerializer


class SendOTPView(APIView):
    # Make explicit: this endpoint is public / does not require authentication
    permission_classes = [AllowAny]

    def post(self, request):
        # validate input via serializer if available
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]

        # generate OTP (use helper if available, otherwise fallback)
        try:
            otp_code = generate_otp()
        except Exception:
            otp_code = str(random.randint(100000, 999999))

        # save OTP entry
        OTP.objects.create(phone=phone, otp=otp_code)

        # send email (console backend is fine for dev) and also print to console
        try:
            # If you want to email to the user, replace recipient_list with actual email.
            send_mail(
                subject="Your MedQueue AI OTP",
                message=f"Your login OTP is: {otp_code}",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@medqueue.ai")],
                fail_silently=True,
            )
        except Exception:
            # fail_silently so OTP still works even if email fails
            pass

        # Always print OTP in server console for development / debugging
        print("\n======== OTP SENT ========")
        print(f"Phone: {phone}")
        print(f"OTP:   {otp_code}")
        print("===========================\n")

        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    # Make explicit: this endpoint is public / does not require authentication
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input via serializer if available
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Prefer serializer-provided otp_obj if serializer resolves it
        otp_obj = serializer.validated_data.get("otp_obj", None)
        phone = serializer.validated_data.get("phone", None)
        otp_value = serializer.validated_data.get("otp", None)

        # If serializer didn't provide otp_obj, do a manual lookup
        if otp_obj is None:
            if not phone or not otp_value:
                return Response({"error": "Phone and OTP required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                otp_obj = OTP.objects.filter(phone=phone).latest("created_at")
            except OTP.DoesNotExist:
                return Response({"error": "OTP not found"}, status=status.HTTP_404_NOT_FOUND)

            # If serializer didn't already give phone/otp, set them
            phone = phone or otp_obj.phone
            otp_value = otp_value or otp_obj.otp

        # Check expiration (5 minutes)
        if timezone.now() > otp_obj.created_at + timedelta(minutes=5):
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        # Check already used
        if getattr(otp_obj, "is_used", False):
            return Response({"error": "OTP already used"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate code
        if str(otp_value) != str(otp_obj.otp):
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # mark used
        otp_obj.is_used = True
        otp_obj.save(update_fields=["is_used"])

        # create or get user (username default to phone if not present)
        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={"username": phone}
        )

        # Optionally respond with basic user info (do NOT return password!)
        return Response({
            "message": "OTP verified successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "phone": user.phone
            },
            "created": created
        }, status=status.HTTP_200_OK)
