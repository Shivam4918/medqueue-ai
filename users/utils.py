from django.shortcuts import redirect


def redirect_user_dashboard(user):
    """
    Centralized post-login redirect logic.
    Used after successful authentication.
    """

    if user.is_superuser:
        return redirect("/admin/dashboard/")

    role = getattr(user, "role", None)

    if role == "patient":
        return redirect("/dashboard/patient/")

    if role == "doctor":
        return redirect("/dashboard/doctor/")

    if user.role == "receptionist":
        return redirect("/dashboard/receptionist/")

    if role == "hospital_admin":
        return redirect("/hospitals/dashboard/")

    # Fallback
    return redirect("/")
