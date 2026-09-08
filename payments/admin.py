from django.contrib import admin
from .models import Subscription, Payment, Invoice

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "amount", "status", "payment_status", "lifetime", "remaining_days", "created_at")
    list_filter = ("plan", "status", "payment_status", "lifetime")
    search_fields = ("user__email", "user__first_name", "user__last_name", "invoice_number")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "gateway", "status", "utr_number", "created_at")
    list_filter = ("gateway", "status")
    search_fields = ("user__email", "utr_number", "transaction_id", "order_id")

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "user", "total", "payment_status", "created_at")
    list_filter = ("payment_status",)
    search_fields = ("invoice_number", "user__email")
