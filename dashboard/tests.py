# dashboard/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardRBACSmokeTest(TestCase):
    """
    Production RBAC smoke tests for MedQueue AI
    """

    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient1",
            password="pass1234",
            role="patient"
        )

        self.doctor = User.objects.create_user(
            username="doctor1",
            password="pass1234",
            role="doctor"
        )

        self.receptionist = User.objects.create_user(
            username="reception1",
            password="pass1234",
            role="receptionist"
        )

        self.hospital_admin = User.objects.create_user(
            username="hospital1",
            password="pass1234",
            role="hospital_admin"
        )

        self.superuser = User.objects.create_superuser(
            username="super1",
            password="pass1234",
            email="super@test.com"
        )

    # ===============================
    # PORTAL LOGIN (STEP 2)
    # ===============================

    def test_patient_login_via_patient_portal(self):
        response = self.client.post(
            "/auth/patient/login/",
            {"username": "patient1", "password": "pass1234"},
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_patient_blocked_from_doctor_portal(self):
        response = self.client.post(
            "/auth/doctor/login/",
            {"username": "patient1", "password": "pass1234"},
            follow=True
        )
        self.assertContains(response, "Unauthorized")

    def test_superuser_blocked_from_domain_portal(self):
        response = self.client.post(
            "/auth/patient/login/",
            {"username": "super1", "password": "pass1234"},
            follow=True
        )
        self.assertContains(response, "admin")

    # ===============================
    # DASHBOARD ACCESS (STEP 3)
    # ===============================

    def test_patient_can_access_patient_dashboard(self):
        self.client.login(username="patient1", password="pass1234")
        response = self.client.get("/dashboard/patient/")
        self.assertEqual(response.status_code, 200)

    def test_patient_blocked_from_doctor_dashboard(self):
        self.client.login(username="patient1", password="pass1234")
        response = self.client.get("/dashboard/doctor/", follow=True)
        self.assertNotEqual(response.status_code, 200)

    def test_doctor_can_access_doctor_dashboard(self):
        self.client.login(username="doctor1", password="pass1234")
        response = self.client.get("/dashboard/doctor/")
        self.assertEqual(response.status_code, 200)

    def test_superuser_blocked_from_dashboards(self):
        self.client.login(username="super1", password="pass1234")
        response = self.client.get("/dashboard/patient/", follow=True)
        self.assertRedirects(response, "/admin/")
