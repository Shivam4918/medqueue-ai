# users/forms.py

from django import forms
from .models import User


class ReceptionistProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "notifications_enabled",
        ]