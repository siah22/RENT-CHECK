from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from engagement.models import Favorite, Report
from engagement.utils import notify
from properties.models import Property

from .decorators import admin_required


def home(request):
    listings = Property.objects.filter(
        is_available=True, is_rented=False, verification_status=Property.VerificationStatus.APPROVED
    ).prefetch_related("images").order_by("-date_listed")

    paginator = Paginator(listings, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(tenant=request.user).values_list("property_id", flat=True)
        )

    return render(request, "core/home.html", {
        "page_obj": page_obj,
        "favorite_ids": favorite_ids,
        "property_types": Property.PropertyType.choices,
    })


@admin_required
def dashboard(request):
    stats = {
        "total_users": User.objects.count(),
        "total_tenants": User.objects.filter(role=User.Role.TENANT).count(),
        "total_owners": User.objects.filter(role=User.Role.OWNER_AGENT).count(),
        "total_properties": Property.objects.count(),
        "verified_properties": Property.objects.filter(
            verification_status=Property.VerificationStatus.APPROVED).count(),
        "pending_properties": Property.objects.filter(
            verification_status=Property.VerificationStatus.PENDING).count(),
        "reported_properties": Report.objects.filter(status=Report.Status.PENDING).count(),
        "active_listings": Property.objects.filter(is_available=True, is_rented=False).count(),
    }
    return render(request, "core/dashboard.html", {"stats": stats})


@admin_required
def dashboard_properties(request):
    status = request.GET.get("status", Property.VerificationStatus.PENDING)
    listings = Property.objects.select_related("owner").order_by("-date_listed")
    if status:
        listings = listings.filter(verification_status=status)
    return render(request, "core/dashboard_properties.html", {
        "listings": listings, "current_status": status,
        "statuses": Property.VerificationStatus.choices,
    })


@admin_required
def dashboard_property_action(request, pk, action):
    property_obj = get_object_or_404(Property, pk=pk)
    if action == "approve":
        property_obj.verification_status = Property.VerificationStatus.APPROVED
        property_obj.rejection_reason = ""
        messages.success(request, f"'{property_obj.title}' approved and verified.")
        notify(property_obj.owner, f"Your listing '{property_obj.title}' has been verified and approved.",
               property_obj.get_absolute_url())
    elif action == "reject":
        property_obj.verification_status = Property.VerificationStatus.REJECTED
        property_obj.rejection_reason = request.POST.get("reason", "")
        messages.success(request, f"'{property_obj.title}' rejected.")
        notify(property_obj.owner, f"Your listing '{property_obj.title}' was rejected during verification.",
               property_obj.get_absolute_url())
    else:
        messages.error(request, "Unknown action.")
        return redirect("core:dashboard_properties")
    property_obj.save()
    return redirect("core:dashboard_properties")


@admin_required
def dashboard_reports(request):
    status = request.GET.get("status", Report.Status.PENDING)
    reports = Report.objects.select_related("property", "reporter").order_by("-date_reported")
    if status:
        reports = reports.filter(status=status)
    return render(request, "core/dashboard_reports.html", {
        "reports": reports, "current_status": status, "statuses": Report.Status.choices,
    })


@admin_required
def dashboard_report_action(request, pk, new_status):
    from django.utils import timezone
    report = get_object_or_404(Report, pk=pk)
    if new_status not in Report.Status.values:
        messages.error(request, "Unknown status.")
        return redirect("core:dashboard_reports")
    report.status = new_status
    report.resolved_at = timezone.now()
    report.save()
    notify(report.reporter, f"Your report on '{report.property.title}' was marked as {report.get_status_display().lower()}.",
           report.property.get_absolute_url())
    messages.success(request, "Report updated.")
    return redirect("core:dashboard_reports")


@admin_required
def dashboard_users(request):
    users = User.objects.exclude(is_superuser=True).order_by("-created_at")
    return render(request, "core/dashboard_users.html", {"users": users})


@admin_required
def dashboard_toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.account_status = (
        User.Status.SUSPENDED if user.account_status == User.Status.ACTIVE else User.Status.ACTIVE
    )
    user.is_active = user.account_status == User.Status.ACTIVE
    user.save()
    messages.success(request, f"{user.username} is now {user.get_account_status_display().lower()}.")
    return redirect("core:dashboard_users")
