from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["pk", "user", "amount", "purpose", "status", "reference", "created_at"]
    list_filter = ["status", "purpose", "created_at"]
    search_fields = ["reference", "conversation_id", "transaction_id", "user__username", "phone"]
    readonly_fields = ["conversation_id", "transaction_id", "provider_response", "created_at", "updated_at"]