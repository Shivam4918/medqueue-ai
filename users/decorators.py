from functools import wraps
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            if request.user.role != required_role:
                messages.error(request, "Access denied")
                return redirect("/")

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
