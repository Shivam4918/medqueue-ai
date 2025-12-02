from rest_framework import serializers
from .models import Hospital

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ["id", "name", "address", "city", "contact_phone", "timezone", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
