from django import forms
from django.utils import timezone

from .models import Booking, Inquiry, Report, Review, ViewingRequest


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4,
                                              "placeholder": "Ask a question about this property..."}),
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
                                              "placeholder": "Anything the host should know? (optional)"}),
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
            "placeholder": "Type a message...",
        }),
    )


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "description"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                                   "placeholder": "Provide more details (optional)"}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(1, 6)],
                                    attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
