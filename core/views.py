from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.models import User
from engagement.models import Favorite, Report
from engagement.utils import notify
from properties.models import Property

from .decorators import admin_required


def home(request):
    if request.user.is_authenticated and request.user.is_admin_role and not request.GET.get("preview"):
        return redirect("core:dashboard")

    listings = Property.objects.filter(
        is_available=True, verification_status=Property.VerificationStatus.APPROVED
    ).filter(
        models.Q(is_rented=False) | models.Q(property_type=Property.PropertyType.BNB)
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
    # Ensure current admin has correct role
    if request.user.is_superuser and request.user.role != User.Role.ADMIN:
        request.user.role = User.Role.ADMIN
        request.user.save(update_fields=["role"])

    total_users = User.objects.count()
    total_tenants = User.objects.filter(role=User.Role.TENANT).exclude(is_superuser=True).exclude(is_staff=True).count()
    total_owners = User.objects.filter(role=User.Role.OWNER_AGENT).count()
    total_admins = User.objects.filter(
        models.Q(role=User.Role.ADMIN) | models.Q(is_superuser=True) | models.Q(is_staff=True)
    ).distinct().count()

    total_properties = Property.objects.count()
    verified_properties = Property.objects.filter(
        verification_status=Property.VerificationStatus.APPROVED
    ).count()
    pending_properties = Property.objects.filter(
        verification_status=Property.VerificationStatus.PENDING
    ).count()
    rejected_properties = Property.objects.filter(
        verification_status=Property.VerificationStatus.REJECTED
    ).count()
    active_listings = Property.objects.filter(is_available=True, is_rented=False).count()

    pending_reports = Report.objects.filter(status=Report.Status.PENDING).count()
    total_reports = Report.objects.count()

    # Recent pending listings for 1-click verification directly on the dashboard
    recent_pending = Property.objects.filter(
        verification_status=Property.VerificationStatus.PENDING
    ).select_related("owner").prefetch_related("images").order_by("-date_listed")[:5]

    # Recent pending reports for immediate review
    recent_reports = Report.objects.filter(
        status=Report.Status.PENDING
    ).select_related("property", "reporter").order_by("-date_reported")[:5]

    # Recent user registrations
    recent_users = User.objects.order_by("-date_joined")[:6]

    stats = {
        "total_users": total_users,
        "total_tenants": total_tenants,
        "total_owners": total_owners,
        "total_admins": total_admins,
        "total_properties": total_properties,
        "verified_properties": verified_properties,
        "pending_properties": pending_properties,
        "rejected_properties": rejected_properties,
        "active_listings": active_listings,
        "pending_reports": pending_reports,
        "total_reports": total_reports,
    }

    return render(request, "core/dashboard.html", {
        "stats": stats,
        "recent_pending": recent_pending,
        "recent_reports": recent_reports,
        "recent_users": recent_users,
    })


@admin_required
def dashboard_properties(request):
    status = request.GET.get("status", Property.VerificationStatus.PENDING)
    listings = Property.objects.select_related("owner").prefetch_related("images").order_by("-date_listed")
    if status:
        listings = listings.filter(verification_status=status)

    status_counts = {
        "ALL": Property.objects.count(),
        "PENDING": Property.objects.filter(verification_status=Property.VerificationStatus.PENDING).count(),
        "APPROVED": Property.objects.filter(verification_status=Property.VerificationStatus.APPROVED).count(),
        "REJECTED": Property.objects.filter(verification_status=Property.VerificationStatus.REJECTED).count(),
    }

    return render(request, "core/dashboard_properties.html", {
        "listings": listings,
        "current_status": status,
        "statuses": Property.VerificationStatus.choices,
        "status_counts": status_counts,
    })


@admin_required
def dashboard_property_action(request, pk, action):
    property_obj = get_object_or_404(Property, pk=pk)
    if action == "approve":
        property_obj.verification_status = Property.VerificationStatus.APPROVED
        property_obj.rejection_reason = ""
        messages.success(request, _("Listing '%(title)s' verified and approved.") % {"title": property_obj.title})
        notify(property_obj.owner, f"Your listing '{property_obj.title}' has been verified and approved.",
               property_obj.get_absolute_url())
    elif action == "reject":
        property_obj.verification_status = Property.VerificationStatus.REJECTED
        property_obj.rejection_reason = request.POST.get("reason", "").strip() or "Listing details did not meet platform verification guidelines."
        messages.success(request, _("Listing '%(title)s' rejected.") % {"title": property_obj.title})
        notify(property_obj.owner, f"Your listing '{property_obj.title}' was rejected during verification: {property_obj.rejection_reason}",
               property_obj.get_absolute_url())
    else:
        messages.error(request, _("Unknown action."))
        return redirect("core:dashboard_properties")
    property_obj.save()

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("core:dashboard_properties")


@admin_required
def dashboard_reports(request):
    status = request.GET.get("status", Report.Status.PENDING)
    reports = Report.objects.select_related("property", "reporter").order_by("-date_reported")
    if status:
        reports = reports.filter(status=status)

    status_counts = {
        "ALL": Report.objects.count(),
        "PENDING": Report.objects.filter(status=Report.Status.PENDING).count(),
        "REVIEWED": Report.objects.filter(status=Report.Status.REVIEWED).count(),
        "ACTIONED": Report.objects.filter(status=Report.Status.ACTIONED).count(),
        "DISMISSED": Report.objects.filter(status=Report.Status.DISMISSED).count(),
    }

    return render(request, "core/dashboard_reports.html", {
        "reports": reports,
        "current_status": status,
        "statuses": Report.Status.choices,
        "status_counts": status_counts,
    })


@admin_required
def dashboard_report_action(request, pk, new_status):
    report = get_object_or_404(Report, pk=pk)
    if new_status not in Report.Status.values:
        messages.error(request, _("Unknown status."))
        return redirect("core:dashboard_reports")
    report.status = new_status
    report.resolved_at = timezone.now()
    report.save()
    notify(report.reporter, _("Your report on '%(title)s' was marked as %(status)s.") % {"title": report.property.title, "status": report.get_status_display().lower()},
           report.property.get_absolute_url())
    messages.success(request, _("Report updated to %(status)s.") % {"status": report.get_status_display()})

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("core:dashboard_reports")


@admin_required
def dashboard_users(request):
    search_q = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "").strip()
    users = User.objects.order_by("-date_joined")
    if search_q:
        users = users.filter(
            models.Q(username__icontains=search_q) |
            models.Q(email__icontains=search_q) |
            models.Q(first_name__icontains=search_q) |
            models.Q(last_name__icontains=search_q)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    role_counts = {
        "ALL": User.objects.count(),
        "TENANT": User.objects.filter(role=User.Role.TENANT).exclude(is_superuser=True).exclude(is_staff=True).count(),
        "OWNER_AGENT": User.objects.filter(role=User.Role.OWNER_AGENT).count(),
        "ADMIN": User.objects.filter(models.Q(role=User.Role.ADMIN) | models.Q(is_superuser=True) | models.Q(is_staff=True)).distinct().count(),
    }

    return render(request, "core/dashboard_users.html", {
        "users": users,
        "search_q": search_q,
        "role_filter": role_filter,
        "role_counts": role_counts,
    })


@admin_required
def dashboard_toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, _("Superuser accounts cannot be suspended."))
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("core:dashboard_users")

    user.account_status = (
        User.Status.SUSPENDED if user.account_status == User.Status.ACTIVE else User.Status.ACTIVE
    )
    user.is_active = user.account_status == User.Status.ACTIVE
    user.save()
    messages.success(request, _("User '%(username)s' is now %(status)s.") % {"username": user.username, "status": user.get_account_status_display().lower()})

    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("core:dashboard_users")
