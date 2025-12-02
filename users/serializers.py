from rest_framework import serializers
from .models import OTP, User
from django.utils import timezone
import datetime


class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Invalid phone number")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()

    def validate(self, data):
        phone = data.get("phone")
        otp = data.get("otp")

        try:
            otp_obj = OTP.objects.filter(phone=phone, otp=otp, is_used=False).latest("created_at")
        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")

        # OTP expiry (5 minutes)
        if timezone.now() - otp_obj.created_at > datetime.timedelta(minutes=5):
            raise serializers.ValidationError("OTP expired")

        data["otp_obj"] = otp_obj
        return data
