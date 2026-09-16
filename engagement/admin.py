from django.contrib import admin

from .models import (Application, ApplicationScreening, Booking, Favorite,
                     Inquiry, Notification, Report, Review, ViewingRequest)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["tenant", "property", "date_added"]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ["tenant", "owner", "property", "status", "created_at"]
    list_filter = ["status"]


@admin.register(ViewingRequest)
class ViewingRequestAdmin(admin.ModelAdmin):
    list_display = ["tenant", "property", "preferred_date", "preferred_time", "status"]
    list_filter = ["status"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["tenant", "property", "check_in", "check_out", "guests", "status"]
    list_filter = ["status"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["reporter", "property", "reason", "status", "date_reported"]
    list_filter = ["status", "reason"]
    actions = ["mark_reviewed", "mark_actioned", "mark_dismissed"]

    @admin.action(description="Mark selected reports as reviewed")
    def mark_reviewed(self, request, queryset):
        queryset.update(status=Report.Status.REVIEWED)

    @admin.action(description="Mark selected reports as actioned")
    def mark_actioned(self, request, queryset):
        queryset.update(status=Report.Status.ACTIONED)

    @admin.action(description="Dismiss selected reports")
    def mark_dismissed(self, request, queryset):
        queryset.update(status=Report.Status.DISMISSED)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "property", "rating", "date"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "message", "is_read", "created_at"]
    list_filter = ["is_read"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["full_name", "property", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["full_name", "phone", "email", "property__title"]


@admin.register(ApplicationScreening)
class ApplicationScreeningAdmin(admin.ModelAdmin):
    list_display = ["application", "score", "passed", "updated_at"]