from django import forms

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
            "price", "bedrooms", "bathrooms", "size_sqm", "amenities",
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
        }
        help_texts = {
            "price": "Monthly rent, or price per night for Airbnb / Short Stay listings.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Amenity.objects.exists():
            for name in ["Water", "Electricity", "Parking", "Security", "Furnished",
                         "Internet", "Backup Generator", "Fenced Compound"]:
                Amenity.objects.get_or_create(name=name)
        self.fields["amenities"].queryset = Amenity.objects.all()


class PropertySearchForm(forms.Form):
    q = forms.CharField(required=False, label="Keyword",
                         widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Location, title..."}))
    property_type = forms.ChoiceField(
        required=False,
        choices=[("", "Any type")] + list(Property.PropertyType.choices),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    min_price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": "Min price"}))
    max_price = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": "Max price"}))
    bedrooms = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": "Min bedrooms"}))
    bathrooms = forms.IntegerField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": "Min bathrooms"}))
    min_size = forms.DecimalField(required=False, widget=forms.NumberInput(
        attrs={"class": "form-control", "placeholder": "Min size (sqm)"}))
    amenities = forms.ModelMultipleChoiceField(
        required=False, queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ("-date_listed", "Newest first"),
            ("price", "Price: low to high"),
            ("-price", "Price: high to low"),
            ("-size_sqm", "Size: largest first"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )