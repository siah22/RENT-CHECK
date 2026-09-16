from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Amenity, Property


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        upload = files.getlist(name)
        if not upload:
            return None
        return upload


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class PropertyForm(forms.ModelForm):
    images = MultipleFileField(required=False, help_text="You may select multiple images.")

    class Meta:
        model = Property
        fields = [
            "title", "description", "property_type", "region", "city", "address",
            "price", "bedrooms", "bathrooms", "size_sqm", "amenities", "tenancy_rules",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "property_type": forms.Select(attrs={"class": "form-select"}),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "bedrooms": forms.NumberInput(attrs={"class": "form-control"}),
            "bathrooms": forms.NumberInput(attrs={"class": "form-control"}),
            "size_sqm": forms.NumberInput(attrs={"class": "form-control"}),
            "amenities": forms.CheckboxSelectMultiple(),
            "tenancy_rules": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
        }
        help_texts = {
            "price": _("Monthly rent, or price per night for Airbnb / Short Stay listings."),
            "tenancy_rules": _("Rules tenants agree to when applying (deposit, notice period, house rules, etc.)."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Amenity.objects.exists():
            for name in ["Water", "Electricity", "Parking", "Security", "Furnished",
                         "Internet", "Backup Generator", "Fenced Compound"]:
                Amenity.objects.get_or_create(name=name)
        self.fields["amenities"].queryset = Amenity.objects.all()


class PropertySearchForm(forms.Form):
    q = forms.CharField(required=False, label=_("Keyword"),
                         widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Location, title...")}))
    property_type = forms.ChoiceField(
        required=False,
        choices=[("", _("Any type"))] + list(Property.PropertyType.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": _("Min price")}))
    max_price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": _("Max price")}))
    bedrooms = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": _("Min bedrooms")}))
    bathrooms = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": _("Min bathrooms")}))
    min_size = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": _("Min size (sqm)")}))
    amenities = forms.ModelMultipleChoiceField(
        required=False, queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("-date_listed", _("Newest first")),
            ("price", _("Price: low to high")),
            ("-price", _("Price: high to low")),
            ("-size_sqm", _("Size: largest first")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )