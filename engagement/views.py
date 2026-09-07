from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.decorators import owner_agent_required
from properties.models import Property

from .forms import BookingForm, InquiryForm, InquiryResponseForm, ReportForm, ReviewForm, ViewingRequestForm
from .models import Booking, Favorite, Inquiry, Notification, Report, Review, ViewingRequest
from .utils import notify


@login_required
def toggle_favorite(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    favorite, created = Favorite.objects.get_or_create(tenant=request.user, property=property_obj)
    if not created:
        favorite.delete()
        messages.info(request, "Removed from favorites.")
    else:
        messages.success(request, "Added to favorites.")
    return redirect(request.META.get("HTTP_REFERER", property_obj.get_absolute_url()))


@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(tenant=request.user).select_related("property")
    favorite_ids = set(favorites.values_list("property_id", flat=True))
    return render(request, "engagement/favorite_list.html", {
        "favorites": favorites, "favorite_ids": favorite_ids,
    })


@login_required
def send_inquiry(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.tenant = request.user
            inquiry.owner = property_obj.owner
            inquiry.property = property_obj
            inquiry.save()
            notify(property_obj.owner, f"New inquiry on '{property_obj.title}'", property_obj.get_absolute_url())
            messages.success(request, "Your inquiry has been sent to the owner/agent.")
            return redirect("properties:detail", pk=pk)
    else:
        form = InquiryForm()
    return render(request, "engagement/inquiry_form.html", {"form": form, "property": property_obj})


@login_required
def inquiry_list(request):
    sent = Inquiry.objects.filter(tenant=request.user).select_related("property")
    received = Inquiry.objects.filter(owner=request.user).select_related("property", "tenant")
    return render(request, "engagement/inquiry_list.html", {"sent": sent, "received": received})


@owner_agent_required
def respond_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk, owner=request.user)
    if request.method == "POST":
        form = InquiryResponseForm(request.POST, instance=inquiry)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.status = Inquiry.Status.RESPONDED
            inquiry.responded_at = timezone.now()
            inquiry.save()
            notify(inquiry.tenant, f"Your inquiry on '{inquiry.property.title}' received a response",
                   inquiry.property.get_absolute_url())
            messages.success(request, "Response sent.")
            return redirect("engagement:inquiry_list")
    else:
        form = InquiryResponseForm(instance=inquiry)
    return render(request, "engagement/inquiry_respond.html", {"form": form, "inquiry": inquiry})


@login_required
def request_viewing(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        form = ViewingRequestForm(request.POST)
        if form.is_valid():
            viewing = form.save(commit=False)
            viewing.tenant = request.user
            viewing.property = property_obj
            viewing.save()
            notify(property_obj.owner, f"New viewing request for '{property_obj.title}'",
                   property_obj.get_absolute_url())
            messages.success(request, "Viewing request submitted.")
            return redirect("properties:detail", pk=pk)
    else:
        form = ViewingRequestForm()
    return render(request, "engagement/viewing_form.html", {"form": form, "property": property_obj})


@login_required
def viewing_list(request):
    if request.user.is_owner_agent:
        viewings = ViewingRequest.objects.filter(property__owner=request.user).select_related(
            "property", "tenant"
        )
    else:
        viewings = ViewingRequest.objects.filter(tenant=request.user).select_related("property")
    return render(request, "engagement/viewing_list.html", {"viewings": viewings})


@owner_agent_required
def update_viewing_status(request, pk, new_status):
    viewing = get_object_or_404(ViewingRequest, pk=pk, property__owner=request.user)
    if new_status not in (ViewingRequest.Status.ACCEPTED, ViewingRequest.Status.REJECTED):
        messages.error(request, "Invalid status.")
        return redirect("engagement:viewing_list")
    viewing.status = new_status
    viewing.save()
    notify(viewing.tenant, f"Your viewing request for '{viewing.property.title}' was {new_status.lower()}",
           viewing.property.get_absolute_url())
    messages.success(request, f"Viewing request {new_status.lower()}.")
    return redirect("engagement:viewing_list")


@login_required
def request_booking(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tenant = request.user
            booking.property = property_obj
            booking.save()
            notify(property_obj.owner, f"New booking request for '{property_obj.title}'",
                   property_obj.get_absolute_url())
            messages.success(request, "Booking request submitted.")
            return redirect("properties:detail", pk=pk)
    else:
        form = BookingForm()
    return render(request, "engagement/booking_form.html", {"form": form, "property": property_obj})


@login_required
def booking_list(request):
    if request.user.is_owner_agent:
        bookings = Booking.objects.filter(property__owner=request.user).select_related("property", "tenant")
    else:
        bookings = Booking.objects.filter(tenant=request.user).select_related("property")
    return render(request, "engagement/booking_list.html", {"bookings": bookings})


@owner_agent_required
def update_booking_status(request, pk, new_status):
    booking = get_object_or_404(Booking, pk=pk, property__owner=request.user)
    if new_status not in (Booking.Status.CONFIRMED, Booking.Status.REJECTED):
        messages.error(request, "Invalid status.")
        return redirect("engagement:booking_list")
    booking.status = new_status
    booking.save()
    notify(booking.tenant, f"Your booking for '{booking.property.title}' was {new_status.lower()}",
           booking.property.get_absolute_url())
    messages.success(request, f"Booking {new_status.lower()}.")
    return redirect("engagement:booking_list")


@login_required
def report_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.property = property_obj
            report.save()
            messages.success(request, "Thank you, your report has been submitted for review.")
            return redirect("properties:detail", pk=pk)
    else:
        form = ReportForm()
    return render(request, "engagement/report_form.html", {"form": form, "property": property_obj})


@login_required
def add_review(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    existing = Review.objects.filter(user=request.user, property=property_obj).first()
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=existing)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.property = property_obj
            review.save()
            messages.success(request, "Your review has been posted.")
            return redirect("properties:detail", pk=pk)
    else:
        form = ReviewForm(instance=existing)
    return render(request, "engagement/review_form.html", {"form": form, "property": property_obj})


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "engagement/notification_list.html", {"notifications": notifications})
