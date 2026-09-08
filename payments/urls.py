from django.urls import path
from . import views
from . import api_views
from . import admin_promo_views

urlpatterns = [
    # Core Billing & Subscription Checkout
    path("billing/", views.billing, name="billing"),
    path("checkout/", views.billing_checkout, name="billing_checkout_default"),
    path("checkout/<int:subscription_id>/", views.billing_checkout, name="billing_checkout"),
    path("change-plan/<int:subscription_id>/", views.change_plan_checkout, name="change_plan_checkout"),
    path("razorpay/create-order/", views.razorpay_create_order, name="razorpay_create_order"),
    path("razorpay/verify/", views.razorpay_verify_payment, name="razorpay_verify_payment"),
    path("qr-submit/<int:subscription_id>/", views.qr_submit_verification, name="qr_submit_verification"),
    path("invoice/<int:invoice_id>/download/", views.download_invoice, name="download_invoice"),
    path("payment-succeed/", views.payment_success, name="payment-succeed"),
    path("payment-failed/", views.payment_failed, name="payment_failed"),
    path("subscription-required/", views.subscription_required, name="subscription_required"),
    path("subscription-expired/", views.subscription_expired, name="subscription_expired"),

    # Public Promo Code APIs
    path("api/promo/validate/", api_views.validate_promo_api, name="promo_validate_api"),
    path("api/promo/apply/", api_views.apply_promo_api, name="promo_apply_api"),
    path("api/promo/remove/", api_views.remove_promo_api, name="promo_remove_api"),
    path("api/promo/auto-apply/", api_views.auto_apply_promo_api, name="promo_auto_apply_api"),
    path("api/promo/free-checkout/", api_views.free_checkout_api, name="promo_free_checkout_api"),

    # Custom Superuser Admin Subscription Dashboard
    path("admin/dashboard/", views.admin_subscription_dashboard, name="admin_subscription_dashboard"),
    path("admin/api/subscriptions/search/", views.admin_subscription_search_api, name="admin_subscription_search_api"),
    path("admin/approve-qr/<int:payment_id>/", views.admin_approve_qr, name="admin_approve_qr"),
    path("admin/reject-qr/<int:payment_id>/", views.admin_reject_qr, name="admin_reject_qr"),
    path("admin/extend/<int:subscription_id>/", views.admin_extend_subscription, name="admin_extend_subscription"),
    path("admin/convert-lifetime/<int:subscription_id>/", views.admin_convert_lifetime, name="admin_convert_lifetime"),
    path("admin/cancel/<int:subscription_id>/", views.admin_cancel_subscription, name="admin_cancel_subscription"),

    # Admin Promo Code Management Module
    path("admin/promos/", admin_promo_views.admin_promo_dashboard, name="admin_promo_dashboard"),
    path("admin/promos/create/", admin_promo_views.admin_promo_create, name="admin_promo_create"),
    path("admin/promos/<int:promo_id>/edit/", admin_promo_views.admin_promo_edit, name="admin_promo_edit"),
    path("admin/promos/<int:promo_id>/duplicate/", admin_promo_views.admin_promo_duplicate, name="admin_promo_duplicate"),
    path("admin/promos/<int:promo_id>/toggle/", admin_promo_views.admin_promo_toggle_status, name="admin_promo_toggle_status"),
    path("admin/promos/<int:promo_id>/archive/", admin_promo_views.admin_promo_archive, name="admin_promo_archive"),
    path("admin/promos/<int:promo_id>/delete/", admin_promo_views.admin_promo_delete, name="admin_promo_delete"),
    path("admin/promos/bulk/", admin_promo_views.admin_promo_bulk_action, name="admin_promo_bulk_action"),
    path("admin/promos/export/", admin_promo_views.admin_promo_export_csv, name="admin_promo_export_csv"),
    path("admin/promos/logs/", admin_promo_views.admin_promo_audit_logs, name="admin_promo_audit_logs"),
]
