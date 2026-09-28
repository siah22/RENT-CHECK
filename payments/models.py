from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Payment(models.Model):
    class Purpose(models.TextChoices):
        DEPOSIT = "DEPOSIT", _("Security deposit / advance rent")
        BOOKING = "BOOKING", _("Booking deposit")
        SERVICE = "SERVICE", _("Listing or service package")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")
        REVERSED = "REVERSED", _("Reversed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    reference = models.CharField(max_length=120, help_text=_("What this payment is for"))
    description = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    conversation_id = models.CharField(max_length=64, blank=True, editable=False)
    transaction_id = models.CharField(max_length=64, blank=True, editable=False)
    provider_response = models.JSONField(default=dict, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.amount} TZS ({self.get_status_display()})"

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED