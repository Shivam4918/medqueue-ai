from rest_framework import serializers
from .models import Doctor
from django.contrib.auth import get_user_model

User = get_user_model()

class UserLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "role"]

class DoctorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role="doctor") | User.objects.all())
    # above allows picking an existing user; adjust if you want to force role check

    class Meta:
        model = Doctor
        fields = ["id", "user", "hospital", "specialization", "opd_start", "opd_end", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        # optional: ensure user doesn't already have a Doctor profile
        user = data.get("user")
        if user and hasattr(user, "doctor_profile"):
            # if trying to create new doctor for user who already linked
            raise serializers.ValidationError({"user": "Selected user already has a doctor profile."})
        return data
