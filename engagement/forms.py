from django import forms

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

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in")
        check_out = cleaned_data.get("check_out")
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("Check-out date must be after the check-in date.")
        return cleaned_data


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
