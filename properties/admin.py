from django.contrib import admin

from .models import Amenity, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "property_type", "city", "price", "verification_status",
                     "is_available", "is_rented", "date_listed"]
    list_filter = ["verification_status", "property_type", "is_available", "is_rented", "region"]
    search_fields = ["title", "city", "region", "owner__username"]
    inlines = [PropertyImageInline]
    actions = ["approve_properties", "reject_properties"]

    @admin.action(description="Approve selected properties")
    def approve_properties(self, request, queryset):
        queryset.update(verification_status=Property.VerificationStatus.APPROVED)

    @admin.action(description="Reject selected properties")
    def reject_properties(self, request, queryset):
        queryset.update(verification_status=Property.VerificationStatus.REJECTED)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ["name"]
