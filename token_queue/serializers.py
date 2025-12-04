# token_queue/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

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
    Admin-style token creation serializer.
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


class TokenBookingSerializer(serializers.Serializer):
    """
    Patient-facing booking serializer (POST /api/token_queue/book/).
    - doctor_id required
    - If user is authenticated and role == 'patient' -> use request.user as patient
    - Else: require 'phone' in request data to create/find patient
    - Validates OPD hours and duplicate active token
    """
    doctor_id = serializers.IntegerField()
    phone = serializers.CharField(required=False, allow_blank=False)  # required for anonymous bookings

    def validate_doctor_id(self, value):
        try:
            Doctor.objects.get(pk=value)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError("Doctor not found.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        doctor_id = attrs.get("doctor_id")
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
        except Doctor.DoesNotExist:
            raise serializers.ValidationError({"doctor_id": "Doctor not found."})

        # OPD hours check (server local time). Consider using hospital timezone later.
        now = timezone.localtime().time()
        start = doctor.opd_start
        end = doctor.opd_end
        if start and end:
            if start <= end:
                if not (start <= now <= end):
                    raise serializers.ValidationError("Doctor is currently outside OPD hours.")
            else:
                # overnight shift (e.g., 22:00 - 06:00)
                if not (now >= start or now <= end):
                    raise serializers.ValidationError("Doctor is currently outside OPD hours.")

        # Resolve patient:
        patient = None
        if request and getattr(request, "user", None) and request.user.is_authenticated:
            # authenticated user path
            if getattr(request.user, "role", None) != "patient":
                raise serializers.ValidationError("Only patients may book tokens (authenticated users must have patient role).")
            patient = request.user
        else:
            # anonymous booking: require phone
            phone = attrs.get("phone")
            if not phone:
                raise serializers.ValidationError({"phone": "Phone is required for anonymous booking."})
            phone = phone.strip()
            patient, created = User.objects.get_or_create(
                phone=phone,
                defaults={"username": phone}
            )
            if created:
                patient.role = "patient"
                patient.set_unusable_password()
                patient.save()

        # Duplicate active token check for this patient
        active_exists = Token.objects.filter(
            patient=patient,
            status__in=["waiting", "in_service"]
        ).exists()
        if active_exists:
            raise serializers.ValidationError("You already have an active token.")

        # Attach resolved objects for view usage
        attrs["patient"] = patient
        attrs["doctor"] = doctor
        attrs["hospital"] = getattr(doctor, "hospital", None)

        return attrs
