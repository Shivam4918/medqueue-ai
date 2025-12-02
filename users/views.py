from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings

from .models import OTP, User, generate_otp
from .serializers import SendOTPSerializer, VerifyOTPSerializer


@api_view(["POST"])
def send_otp(request):
    serializer = SendOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data["phone"]
    otp = generate_otp()

    OTP.objects.create(phone=phone, otp=otp)

    # send email OTP (simple)
    send_mail(
        subject="Your MedQueue AI OTP",
        message=f"Your login OTP is: {otp}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["your-email@example.com"],  # replace later
    )

    return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


@api_view(["POST"])
def verify_otp(request):
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    otp_obj = serializer.validated_data["otp_obj"]

    phone = serializer.validated_data["phone"]

    # Mark OTP as used
    otp_obj.is_used = True
    otp_obj.save()

    # Create or get user
    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={"username": phone}
    )

    return Response({
        "message": "OTP verified successfully",
        "user_id": user.id,
        "phone": user.phone
    }, status=status.HTTP_200_OK)

