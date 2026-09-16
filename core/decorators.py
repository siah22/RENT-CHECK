from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import gettext as _


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, _("You do not have permission to access that page."))
                return redirect("core:home")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def owner_agent_required(view_func):
    from accounts.models import User
    return role_required(User.Role.OWNER_AGENT)(view_func)


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_admin_role):
            messages.error(request, _("Administrator access required."))
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return _wrapped
