from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse


class Amenity(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "amenities"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = "APARTMENT", "Apartment"
        HOUSE = "HOUSE", "House"
        ROOM = "ROOM", "Single Room"
        STUDIO = "STUDIO", "Studio"
        OFFICE = "OFFICE", "Office"
        HOSTEL = "HOSTEL", "Hostel"
        BNB = "BNB", "Airbnb / Short Stay"

    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="properties"
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)

    # Location fields support search/filter by location (FR-07, FR-08)
    region = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    size_sqm = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Approximate size in square metres",
    )
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")

    is_available = models.BooleanField(default=True)
    is_rented = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    rejection_reason = models.CharField(max_length=255, blank=True)

    date_listed = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"
        ordering = ["-date_listed"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("properties:detail", args=[self.pk])

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.APPROVED

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg("rating"))["rating__avg"]
        return round(agg, 1) if agg else None

    @property
    def main_image(self):
        return self.images.first()

    @property
    def is_bnb(self):
        return self.property_type == self.PropertyType.BNB


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="property_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Image for {self.property.title}"
