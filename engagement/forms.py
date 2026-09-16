from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import (Application, ApplicationScreening, Booking, Inquiry,
                     Report, Review, ViewingRequest)


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4,
                                              "placeholder": _("Ask a question about this property...")}),
        }


class InquiryResponseForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["response"]
        widgets = {
            "response": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ViewingRequestForm(forms.ModelForm):
    class Meta:
        model = ViewingRequest
        fields = ["preferred_date", "preferred_time", "message"]
        widgets = {
            "preferred_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "preferred_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["check_in", "check_out", "guests", "message"]
        widgets = {
            "check_in": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "check_out": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "guests": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                              "placeholder": _("Anything the host should know? (optional)")}),
        }

    def __init__(self, *args, property_obj=None, **kwargs):
        self.property_obj = property_obj
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["check_in"].widget.attrs["min"] = today.isoformat()
        self.fields["check_out"].widget.attrs["min"] = today.isoformat()

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")
        if check_in and check_out:
            if check_out <= check_in:
                raise forms.ValidationError("Check-out date must be after the check-in date.")
            if check_in < timezone.localdate():
                raise forms.ValidationError("Check-in cannot be in the past.")
            if self.property_obj and self.property_obj.bookings.filter(
                status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                check_in__lt=check_out,
                check_out__gt=check_in,
            ).exists():
                raise forms.ValidationError(
                    "Those dates overlap an existing booking. Please choose different dates."
                )
        return cleaned_data


class MessageForm(forms.Form):
    body = forms.CharField(
        label="",
        max_length=2000,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": _("Type a message..."),
        }),
    )


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["full_name", "phone", "email", "current_address", "notes"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": _("Full name as shown on your ID")}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. +255 7XX XXX XXX"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "current_address": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                          "placeholder": _("Anything else the owner should know?")}),
        }


class ApplicationScreeningForm(forms.ModelForm):
    class Meta:
        model = ApplicationScreening
        fields = [
            "identity_verified", "income_verified", "references_checked",
            "employment_verified", "background_checked", "score", "notes",
        ]
        widgets = {
            "score": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "description"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                                   "placeholder": _("Provide more details (optional)")}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} {_('star') if i == 1 else _('stars')}") for i in range(1, 6)],
                                    attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
