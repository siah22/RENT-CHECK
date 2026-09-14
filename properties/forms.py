from django import forms
from .models import Property

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'property_type',
            'price',
            'bedrooms',
            'bathrooms',
            'area',
            'address',
            'city',
            'state',
            'zip_code',
            'is_available',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }