from calendar import month_name, monthcalendar, monthrange
from datetime import date as date_cls
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from core.decorators import owner_agent_required
from properties.models import Property

from .forms import (ApplicationForm, ApplicationScreeningForm, BookingForm,
                    InquiryForm, InquiryResponseForm, MessageForm, ReportForm,
                    ReviewForm, ViewingRequestForm)
from .models import (Application, ApplicationAnswer, ApplicationQuestion,
                     ApplicationScreening, Booking, Conversation, Favorite,
                     Inquiry, Message, Notification, Report, Review, ViewingRequest)
from .utils import notify


DEFAULT_APPLICATION_QUESTIONS = (
    ("How long do you intend to rent for?", True),
    ("How many people will be living there?", True),
    ("Do you have any pets?", False),
)


def ensure_application_questions(property_obj):
    """Idempotently add the default application questions to a listing."""
    for text, required in DEFAULT_APPLICATION_QUESTIONS:
        ApplicationQuestion.objects.get_or_create(
            property=property_obj,
            question=text,
            defaults={"required": required, "order": 0},
        )


def booked_dates_for_property(property_obj, days=180):
    """Return the set of date objects that are blocked by active bookings."""
    start = timezone.localdate()
    end = start + timedelta(days=days)
    active = property_obj.bookings.filter(
        status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
        check_in__lt=end,
        check_out__gt=start,
    )
    dates = set()
    for booking in active:
        day = max(booking.check_in, start)
        while day < min(booking.check_out, end):
            dates.add(day)
            day += timedelta(days=1)
    return dates


def build_calendar(blocked_dates, months=3):
    """Build the next N months as calendar cells for the availability widget."""
    today = timezone.localdate()
    first = today.replace(day=1)
    months = []
    for offset in range(months if months else 3):
        year = (first.month - 1 + offset) // 12 + first.year
        month = (first.month - 1 + offset) % 12 + 1
        weeks = []
        for week in monthcalendar(year, month):
            row = []
            for day in week:
                if day == 0:
                    row.append(None)
                else:
                    cell_date = date_cls(year, month, day)
                    row.append({
                        "date": cell_date,
                        "day": day,
                        "booked": cell_date in blocked_dates,
                        "past": cell_date < today,
                    })
            weeks.append(row)
        months.append({
            "year": year,
            "month": month,
            "month_name": month_name[month],
            "weeks": weeks,
        })
    return months


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
    if property_obj.is_rented and property_obj.is_bnb:
        messages.error(request, "This Airbnb is currently booked and not accepting new reservations.")
        return redirect("properties:detail", pk=pk)
    blocked = booked_dates_for_property(property_obj)
    calendar = build_calendar(blocked)
    if request.method == "POST":
        form = BookingForm(request.POST, property_obj=property_obj)
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
        form = BookingForm(property_obj=property_obj)
    return render(request, "engagement/booking_form.html", {
        "form": form,
        "property": property_obj,
        "calendar": calendar,
        "today": timezone.localdate(),
    })


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
def apply_to_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if property_obj.owner == request.user:
        messages.error(request, "You cannot apply to your own listing.")
        return redirect("properties:detail", pk=pk)
    if property_obj.is_rented:
        messages.error(request, "This listing is currently unavailable for applications.")
        return redirect("properties:detail", pk=pk)
    if not (property_obj.is_available and property_obj.is_verified):
        messages.error(request, "This listing is not currently accepting applications.")
        return redirect("properties:detail", pk=pk)

    ensure_application_questions(property_obj)
    questions = property_obj.application_questions.all()

    active = Application.objects.filter(
        tenant=request.user, property=property_obj, status=Application.Status.PENDING
    )
    if active.exists():
        messages.info(request, "You already have a pending application for this listing.")
        return redirect("engagement:application_detail", pk=active.first().pk)

    answers_data = {}
    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.tenant = request.user
            application.property = property_obj
            application.save()
            for question in questions:
                value = request.POST.get(f"question_{question.pk}", "").strip()
                if value:
                    ApplicationAnswer.objects.create(
                        application=application, question=question, answer=value
                    )
            notify(
                property_obj.owner,
                f"New rental application from {application.full_name} for '{property_obj.title}'",
                reverse("engagement:application_detail", args=[application.pk]),
            )
            messages.success(request, "Your application has been submitted to the owner/agent.")
            return redirect("engagement:application_detail", pk=application.pk)
        for question in questions:
            value = request.POST.get(f"question_{question.pk}", "").strip()
            if value:
                answers_data[question.pk] = value
    else:
        form = ApplicationForm(initial={
            "full_name": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
            "phone": request.user.phone_number,
        })
    question_list = [
        {"id": q.pk, "text": q.question, "required": q.required,
         "value": answers_data.get(q.pk, "")}
        for q in questions
    ]
    return render(request, "engagement/application_form.html", {
        "form": form,
        "property": property_obj,
        "question_list": question_list,
    })


@login_required
def application_list(request):
    if request.user.is_owner_agent:
        applications = Application.objects.filter(property__owner=request.user).select_related(
            "property", "tenant"
        )
    else:
        applications = Application.objects.filter(tenant=request.user).select_related("property")
    pending_count = applications.filter(status=Application.Status.PENDING).count()
    return render(request, "engagement/application_list.html", {
        "applications": applications,
        "pending_count": pending_count,
    })


@login_required
def application_detail(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("property", "property__owner", "tenant")
        .prefetch_related("answers", "answers__question"),
        pk=pk,
    )
    if request.user != application.tenant and request.user != application.property.owner:
        messages.error(request, "You do not have access to that application.")
        return redirect("core:home")
    is_owner = request.user == application.property.owner
    return render(request, "engagement/application_detail.html", {
        "application": application,
        "is_owner": is_owner,
    })


@owner_agent_required
def update_application_status(request, pk, new_status):
    application = get_object_or_404(Application, pk=pk, property__owner=request.user)
    if new_status not in (Application.Status.APPROVED, Application.Status.REJECTED):
        messages.error(request, "Invalid status.")
        return redirect("engagement:application_list")
    application.status = new_status
    application.decision_date = timezone.now()
    note = (request.POST.get("note") or "").strip()
    if note:
        application.decision_note = note
    application.save()
    verb = "approved" if new_status == Application.Status.APPROVED else "rejected"
    notify(application.tenant, f"Your application for '{application.property.title}' was {verb}.",
           reverse("engagement:application_detail", args=[application.pk]))
    messages.success(request, f"Application {verb}.")
    return redirect("engagement:application_detail", pk=pk)


@owner_agent_required
def manage_questions(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    ensure_application_questions(property_obj)
    questions = property_obj.application_questions.all()
    if request.method == "POST":
        text = (request.POST.get("question") or "").strip()
        required = request.POST.get("required") == "1"
        if not text:
            messages.error(request, "Question text cannot be empty.")
        elif len(text) > 255:
            messages.error(request, "Question is too long (max 255 characters).")
        else:
            ApplicationQuestion.objects.create(
                property=property_obj, question=text, required=required
            )
            messages.success(request, "Application question added.")
        return redirect("engagement:manage_questions", pk=pk)
    return render(request, "engagement/question_manager.html", {
        "property": property_obj,
        "questions": questions,
    })


@owner_agent_required
def delete_question(request, pk):
    question = get_object_or_404(ApplicationQuestion, pk=pk)
    if question.property.owner != request.user:
        messages.error(request, "You do not have permission to change that question.")
        return redirect("core:home")
    property_pk = question.property.pk
    question.delete()
    messages.success(request, "Application question removed.")
    return redirect("engagement:manage_questions", pk=property_pk)


@owner_agent_required
def toggle_question_required(request, pk):
    question = get_object_or_404(ApplicationQuestion, pk=pk)
    if question.property.owner != request.user:
        messages.error(request, "You do not have permission to change that question.")
        return redirect("core:home")
    question.required = not question.required
    question.save(update_fields=["required"])
    return redirect("engagement:manage_questions", pk=question.property.pk)


@owner_agent_required
def run_screening(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("property"), pk=pk, property__owner=request.user
    )
    screening = ApplicationScreening.objects.filter(application=application).first()
    if request.method == "POST":
        form = ApplicationScreeningForm(request.POST, instance=screening)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.application = application
            instance.save()
            messages.success(request, "Tenant screening saved.")
            return redirect("engagement:application_detail", pk=pk)
    else:
        form = ApplicationScreeningForm(instance=screening)
    return render(request, "engagement/screening_form.html", {
        "form": form,
        "application": application,
    })


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
    unread_ids = list(notifications.filter(is_read=False).values_list("id", flat=True))
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "engagement/notification_list.html", {
        "notifications": notifications,
        "unread_count": len(unread_ids),
        "unread_ids": unread_ids,
    })


@login_required
def notification_delete(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, "Notification deleted.")
    return redirect("engagement:notification_list")


@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(
        Q(tenant=request.user) | Q(owner=request.user)
    ).select_related("listing", "tenant", "owner", "listing__owner")
    return render(request, "engagement/conversation_list.html", {"conversations": conversations})


@login_required
def start_conversation(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    if property_obj.owner == request.user:
        messages.info(request, "You cannot message yourself about your own listing.")
        return redirect("properties:detail", pk=pk)
    conversation, _ = Conversation.objects.get_or_create(
        listing=property_obj,
        tenant=request.user,
        defaults={"owner": property_obj.owner},
    )
    return redirect("engagement:conversation_detail", pk=conversation.pk)


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "tenant", "owner").prefetch_related("messages"),
        pk=pk,
    )
    if request.user not in (conversation.tenant, conversation.owner):
        messages.error(request, "You do not have access to that conversation.")
        return redirect("core:home")

    other_user = conversation.other_user(request.user)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=form.cleaned_data["body"],
            )
            conversation.save()
            notify(
                other_user,
                f"New message from {request.user.username} about '{conversation.listing.title}'",
                reverse("engagement:conversation_detail", args=[conversation.pk]),
            )
            messages.success(request, "Message sent.")
            return redirect("engagement:conversation_detail", pk=conversation.pk)
    else:
        form = MessageForm()

    # WhatsApp-style delivery tracking:
    #  - AJAX polling = the other party's device has received the messages -> DELIVERED
    #  - Normal page load = the other party has actually opened the thread -> READ
    incoming = conversation.messages.filter(~Q(sender=request.user))
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        incoming.filter(is_read=False, status=Message.Status.SENT).update(
            status=Message.Status.DELIVERED
        )
    else:
        incoming.filter(is_read=False).update(status=Message.Status.READ, is_read=True)
    return render(request, "engagement/conversation_detail.html", {
        "conversation": conversation,
        "other_user": other_user,
        "form": form,
    })
