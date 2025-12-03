from django.shortcuts import render

from rest_framework import viewsets
from users.permissions import IsReceptionist, IsDoctor
from .models import Token
from .serializers import TokenSerializer

class TokenViewSet(viewsets.ModelViewSet):
    queryset = Token.objects.all()
    serializer_class = TokenSerializer
    permission_classes = [IsReceptionist | IsDoctor]

