# doctors/serializers.py
from rest_framework import serializers
from .models import Doctor
from django.contrib.auth import get_user_model

User = get_user_model()

class UserLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # include phone/role only if they exist on your User model, otherwise remove them
        fields = ["id", "username", "email", "phone", "role"]


class DoctorSerializer(serializers.ModelSerializer):
    # represent user by PK on write, and optionally nested on read
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    user_detail = UserLiteSerializer(source="user", read_only=True)

    class Meta:
        model = Doctor
        # fields must match your doctors.models: user, hospital, specialization, opd_start, opd_end, created_at, updated_at
        fields = [
            "id",
            "user",
            "user_detail",
            "hospital",
            "specialization",
            "opd_start",
            "opd_end",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_user(self, value):
        """Ensure the selected user does not already have a doctor profile, and optionally check role."""
        # If your User model has a 'role' field and you require role=='doctor', uncomment the block below
        # if getattr(value, "role", None) != "doctor":
        #     raise serializers.ValidationError("Selected user does not have the 'doctor' role.")

        # Prevent assigning a user who already has a doctor_profile
        if hasattr(value, "doctor_profile"):
            raise serializers.ValidationError("Selected user already has a doctor profile.")
        return value

    def validate(self, attrs):
        # Example: ensure hospital is present when required
        # if not attrs.get("hospital"):
        #     raise serializers.ValidationError({"hospital": "Hospital is required for doctor."})
        return super().validate(attrs)
