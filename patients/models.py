# patients/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Patient(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='patient_profile',
        null=True,
        blank=True
    )

    name = models.CharField(max_length=255)

    phone = models.CharField(max_length=20)

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=10,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other")
        ],
        blank=True,
        null=True
    )

    blood_group = models.CharField(
        max_length=5,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True
    )

    emergency_contact = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'patients_patient'
        ordering = ['name']

    def __str__(self):
        return self.name