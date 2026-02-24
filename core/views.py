from django.shortcuts import render, redirect


def public_home(request):
    """
    Universal public landing page.
    If user is already logged in, redirect by role.
    """

    if request.user.is_authenticated:
        role = getattr(request.user, "role", None)

        if role == "patient":
            return redirect("/dashboard/patient/")
        if role == "doctor":
            return redirect("/dashboard/doctor/")
        if role == "receptionist":
            return redirect("/dashboard/receptionist/walkin/")
        if role == "hospital_admin":
            return redirect("/dashboard/hospital/")

        return redirect("/admin/")

    return render(request, "core/home.html")
