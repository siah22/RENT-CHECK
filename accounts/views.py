import hashlib

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.urls import reverse, reverse_lazy

from .forms import ProfileForm, RegistrationForm


class RentCheckLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        redirect_to = self.request.POST.get(self.redirect_field_name) or self.request.GET.get(self.redirect_field_name)
        if redirect_to:
            return redirect_to
        if self.request.user.is_authenticated and self.request.user.is_admin_role:
            return reverse("core:dashboard")
        return super().get_success_url()


class RentCheckLogoutView(LogoutView):
    pass


class SecurePasswordResetView(PasswordResetView):
    """Email-based password reset hardened with a per-IP+email attempt throttle.

    Django's built-in reset flow is already secure (signed, single-use,
    time-limited tokens, no user enumeration, password validators on reset).
    We additionally throttle submissions so a single caller cannot spam the
    reset endpoint or burn through the mail provider.
    """
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.txt"
    html_email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 15 * 60

    def form_valid(self, form):
        raw = f"{self.request.META.get('REMOTE_ADDR', '')}|{form.cleaned_data.get('email', '').lower()}"
        key = "pwreset:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
        attempts = cache.get(key, 0)
        if attempts >= self.MAX_ATTEMPTS:
            form.add_error(
                None,
                "Too many password reset requests from this device. "
                "Please wait about 15 minutes and try again.",
            )
            return self.form_invalid(form)
        cache.set(key, attempts + 1, self.WINDOW_SECONDS)
        return super().form_valid(form)


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("Welcome to RentCheck Tanzania! Your account has been created."))
            return redirect("core:home")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
