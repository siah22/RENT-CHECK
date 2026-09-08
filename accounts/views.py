from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from django.urls import reverse

from .forms import ProfileForm, RegistrationForm


class RentCheckLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        redirect_to = self.get_redirect_field_value()
        if redirect_to:
            return redirect_to
        if self.request.user.is_authenticated and self.request.user.is_admin_role:
            return reverse("core:dashboard")
        return super().get_success_url()


class RentCheckLogoutView(LogoutView):
    pass


def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to RentCheck Tanzania! Your account has been created.")
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
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
