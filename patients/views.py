# patients/views.py
from rest_framework import viewsets
from users.permissions import IsPatient
from .models import Patient
from .serializers import PatientSerializer

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from token_queue.models import Token


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsPatient]
