from django.conf import settings
from django.db import models

from properties.models import Property


class Favorite(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="favorited_by")
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "property")
        ordering = ["-date_added"]

    def __str__(self):
        return f"{self.tenant} ❤ {self.property}"


class Inquiry(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        RESPONDED = "RESPONDED", "Responded"
        CLOSED = "CLOSED", "Closed"

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_inquiries"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_inquiries"
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="inquiries")
    message = models.TextField()
    response = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "inquiries"

    def __str__(self):
        return f"Inquiry by {self.tenant} on {self.property}"


class ViewingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="viewing_requests"
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="viewing_requests")
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Viewing request by {self.tenant} for {self.property}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings"
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking by {self.tenant} for {self.property} ({self.check_in} to {self.check_out})"

    def nights(self):
        return (self.check_out - self.check_in).days

    def total_price(self):
        return self.nights() * self.property.price


class Report(models.Model):
    class Reason(models.TextChoices):
        FAKE_PROPERTY = "FAKE_PROPERTY", "Fake property"
        INCORRECT_INFO = "INCORRECT_INFO", "Incorrect information"
        FAKE_IMAGES = "FAKE_IMAGES", "Fake images"
        INCORRECT_LOCATION = "INCORRECT_LOCATION", "Incorrect location"
        SUSPICIOUS_OWNER = "SUSPICIOUS_OWNER", "Suspicious owner/agent"
        ALREADY_RENTED = "ALREADY_RENTED", "Property already rented"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        ACTIONED = "ACTIONED", "Actioned"
        DISMISSED = "DISMISSED", "Dismissed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_filed"
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reports")
    reason = models.CharField(max_length=30, choices=Reason.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    date_reported = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_reported"]

    def __str__(self):
        return f"Report on {self.property} by {self.reporter}"


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "property")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.rating}★ by {self.user} on {self.property}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message

    @property
    def icon_class(self):
        text = self.message.lower()
        if "message" in text:
            return "bi-chat-left-text-fill"
        if "inquiry" in text:
            return "bi-chat-dots-fill"
        if "viewing" in text:
            return "bi-calendar-check-fill"
        if "booking" in text:
            return "bi-calendar2-check-fill"
        if "report" in text:
            return "bi-flag-fill"
        if any(w in text for w in ("verified", "approved", "rejected", "verification")):
            return "bi-shield-check"
        return "bi-bell-fill"

    @property
    def icon_tone(self):
        text = self.message.lower()
        if any(w in text for w in ("message", "inquiry")):
            return "info"
        if any(w in text for w in ("viewing", "booking")):
            return "gold"
        if "report" in text:
            return "danger"
        if any(w in text for w in ("verified", "approved", "rejected", "verification", "listing")):
            return "success"
        return "primary"


class Conversation(models.Model):
    listing = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="conversations")
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_tenant"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_owner"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("listing", "tenant")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation: {self.tenant} <-> {self.owner} on {self.listing}"

    @property
    def last_message(self):
        return self.messages.last()

    def other_user(self, user):
        return self.owner if user == self.tenant else self.tenant


class Message(models.Model):
    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        DELIVERED = "DELIVERED", "Delivered"
        READ = "READ", "Read"

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_chat_messages"
    )
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SENT
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender} in {self.conversation}"
