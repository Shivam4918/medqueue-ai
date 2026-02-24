from django.shortcuts import redirect


def redirect_user_dashboard(user):
    """
    Centralized post-login redirect logic.
    Used after successful authentication.
    """

    if user.is_superuser:
        return redirect("/admin/")

    role = getattr(user, "role", None)

    if role == "patient":
        return redirect("/dashboard/patient/")

    if role == "doctor":
        return redirect("/dashboard/doctor/")

    if role == "receptionist":
        return redirect("/dashboard/receptionist/walkin/")

    if role == "hospital_admin":
        return redirect("/dashboard/hospital/")

    # Fallback
    return redirect("/")
