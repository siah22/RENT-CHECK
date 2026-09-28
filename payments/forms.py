from django import forms
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

from .models import Payment


class PaymentForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=100,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "100", "min": "100"}),
        label=_("Amount (TZS)"),
        help_text=_("Minimum 100 TZS"),
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "07XXXXXXXX or +2557XXXXXXXX"}
        ),
        label=_("M-Pesa phone number"),
        help_text=_("The M-Pesa number that will approve this payment"),
    )
    purpose = forms.ChoiceField(
        choices=Payment.Purpose.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Purpose"),
    )
    reference = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("e.g. Security deposit — 2-bed flat #12")}
        ),
        label=_("Reference"),
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        label=_("Details (optional)"),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip().replace(" ", "").replace("-", "")
        if phone.startswith("+"):
            phone = phone[1:]
        if phone.startswith("07"):
            phone = "255" + phone[1:]
        if not phone.startswith("255"):
            self.add_error("phone", _("Enter a Tanzanian M-Pesa number, e.g. 0712345678."))
        return phone