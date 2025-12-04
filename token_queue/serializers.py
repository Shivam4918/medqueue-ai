# token_queue/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from hospitals.models import Hospital
from doctors.models import Doctor
from .models import Token

User = get_user_model()


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = "__all__"


class TokenCreateSerializer(serializers.Serializer):
    """
    Accepts either:
     - patient_id (int) OR phone (str) to identify/create patient
     - doctor_id (int) (required)
     - hospital_id (int) (required)
     - priority (int, optional)
    """
    patient_id = serializers.IntegerField(required=False)
    phone = serializers.CharField(required=False, allow_blank=False)
    doctor_id = serializers.IntegerField(required=True)
    hospital_id = serializers.IntegerField(required=True)
    priority = serializers.IntegerField(required=False, default=0)

    def validate(self, attrs):
        # validate doctor
        try:
            doctor = Doctor.objects.get(id=attrs["doctor_id"])
        except (KeyError, Doctor.DoesNotExist):
            raise serializers.ValidationError({"doctor_id": "Doctor not found."})

        # validate hospital
        try:
            hospital = Hospital.objects.get(id=attrs["hospital_id"])
        except (KeyError, Hospital.DoesNotExist):
            raise serializers.ValidationError({"hospital_id": "Hospital not found."})

        # resolve patient
        patient = None
        if attrs.get("patient_id"):
            try:
                patient = User.objects.get(id=attrs["patient_id"])
            except User.DoesNotExist:
                raise serializers.ValidationError({"patient_id": "User not found."})
        elif attrs.get("phone"):
            phone = attrs["phone"].strip()
            # get or create a patient user by phone
            patient, created = User.objects.get_or_create(
                phone=phone,
                defaults={"username": phone}
            )
            if created:
                # set role and make unusable password (you may want a better flow)
                patient.role = "patient"
                patient.set_unusable_password()
                patient.save()
        else:
            raise serializers.ValidationError("Provide patient_id or phone for booking.")

        attrs["patient"] = patient
        attrs["doctor"] = doctor
        attrs["hospital"] = hospital
        return attrs
