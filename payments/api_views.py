import json
import uuid
import decimal
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from .models import Subscription, Payment, Invoice, PromoCode
from .promo_service import (
    validate_promo_code,
    calculate_promo_effect,
    get_auto_apply_promo,
    redeem_promo_atomic
)
from .utils import generate_invoice_pdf
from .middleware import clear_subscription_cache


@login_required
@require_POST
def validate_promo_api(request):
    """
    AJAX endpoint to validate a promo code against a subscription plan and amount.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    code_str = data.get("code", "").strip()
    subscription_id = data.get("subscription_id")
    plan = data.get("plan")

    if subscription_id:
        subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
        plan = plan or subscription.plan
        orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount
    else:
        plan_amounts = {
            "Monthly": decimal.Decimal("499.00"),
            "Yearly": decimal.Decimal("2999.00"),
            "Lifetime": decimal.Decimal("4999.00")
        }
        plan = plan or "Lifetime"
        orig_amount = plan_amounts.get(plan, decimal.Decimal("4999.00"))

    val_res = validate_promo_code(code_str, request.user, plan, orig_amount)
    if not val_res["valid"]:
        return JsonResponse({
            "status": "error",
            "valid": False,
            "error": val_res["error"]
        }, status=200)

    promo = val_res["promo"]
    calc = calculate_promo_effect(promo, orig_amount)

    return JsonResponse({
        "status": "ok",
        "valid": True,
        "code": promo.code,
        "description": promo.description or f"{promo.get_discount_type_display()} promo code",
        "discount_type": promo.discount_type,
        "discount_value": str(promo.discount_value),
        "original_amount": str(calc["original_amount"]),
        "discount_amount": str(calc["discount_amount"]),
        "final_amount": str(calc["final_amount"]),
        "extra_days": calc["extra_days"],
        "is_free": calc["is_free"],
        "summary": calc["summary"]
    })


@login_required
@require_POST
def apply_promo_api(request):
    """
    AJAX endpoint to apply a validated promo code to the user's current session/checkout.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    code_str = data.get("code", "").strip()
    subscription_id = data.get("subscription_id")

    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount

    val_res = validate_promo_code(code_str, request.user, subscription.plan, orig_amount)
    if not val_res["valid"]:
        return JsonResponse({
            "status": "error",
            "message": val_res["error"]
        }, status=400)

    promo = val_res["promo"]
    calc = calculate_promo_effect(promo, orig_amount)

    # Store in session
    request.session["applied_promo_code"] = promo.code
    request.session["applied_promo_subscription_id"] = subscription.id

    return JsonResponse({
        "status": "ok",
        "message": f"Promo code '{promo.code}' applied successfully!",
        "code": promo.code,
        "original_amount": str(calc["original_amount"]),
        "discount_amount": str(calc["discount_amount"]),
        "final_amount": str(calc["final_amount"]),
        "extra_days": calc["extra_days"],
        "is_free": calc["is_free"],
        "summary": calc["summary"]
    })


@login_required
@require_POST
def remove_promo_api(request):
    """
    AJAX endpoint to remove an applied promo code from session/checkout.
    """
    request.session.pop("applied_promo_code", None)
    request.session.pop("applied_promo_subscription_id", None)
    return JsonResponse({"status": "ok", "message": "Promo code removed."})


@login_required
def auto_apply_promo_api(request):
    """
    Endpoint to fetch auto-apply promo code for user's subscription if eligible.
    """
    subscription_id = request.GET.get("subscription_id")
    if not subscription_id:
        return JsonResponse({"status": "error", "message": "Subscription ID required."}, status=400)

    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount

    promo = get_auto_apply_promo(request.user, subscription.plan, orig_amount)
    if not promo:
        return JsonResponse({"status": "ok", "auto_promo": None})

    calc = calculate_promo_effect(promo, orig_amount)
    return JsonResponse({
        "status": "ok",
        "auto_promo": {
            "code": promo.code,
            "description": promo.description,
            "original_amount": str(calc["original_amount"]),
            "discount_amount": str(calc["discount_amount"]),
            "final_amount": str(calc["final_amount"]),
            "extra_days": calc["extra_days"],
            "is_free": calc["is_free"],
            "summary": calc["summary"]
        }
    })


@login_required
@require_POST
def free_checkout_api(request):
    """
    Processes 100% free checkout activation when an applied promo results in final_amount = 0.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    subscription_id = data.get("subscription_id")
    code_str = data.get("code") or request.session.get("applied_promo_code")

    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount

    val_res = validate_promo_code(code_str, request.user, subscription.plan, orig_amount)
    if not val_res["valid"]:
        return JsonResponse({"status": "error", "message": val_res["error"]}, status=400)

    promo = val_res["promo"]
    calc = calculate_promo_effect(promo, orig_amount)

    if not calc["is_free"]:
        return JsonResponse({"status": "error", "message": "This promo code does not grant 100% free access."}, status=400)

    ip_address = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    try:
        with transaction.atomic():
            # Cancel active subscriptions
            Subscription.objects.filter(user=request.user, status="Active").update(status="Cancelled")

            now = timezone.now()
            subscription.start_date = now
            if subscription.plan == "Monthly":
                subscription.end_date = now + timezone.timedelta(days=30)
            elif subscription.plan == "Yearly":
                subscription.end_date = now + timezone.timedelta(days=365)
            else:
                subscription.end_date = None

            subscription.payment_status = "Paid"
            subscription.payment_mode = "100% Free Promo"
            subscription.transaction_id = f"FREE-{promo.code}-{str(uuid.uuid4())[:8].upper()}"

            invoice_id = str(uuid.uuid4())[:8].upper()
            invoice_num = f"RISE360-INV-{now.strftime('%Y%m%d')}-{invoice_id}"
            subscription.invoice_number = invoice_num
            subscription.status = "Active"
            subscription.original_amount = orig_amount
            subscription.save()

            # Create Payment record for 100% free
            payment = Payment.objects.create(
                subscription=subscription,
                user=request.user,
                amount=decimal.Decimal("0.00"),
                discount_amount=orig_amount,
                promo_code=promo,
                gateway="Free Promo",
                transaction_id=subscription.transaction_id,
                status="Success"
            )

            # Create Invoice
            invoice = Invoice.objects.create(
                invoice_number=invoice_num,
                user=request.user,
                subscription=subscription,
                original_amount=orig_amount,
                discount_amount=calc["discount_amount"],
                promo_code_str=promo.code,
                amount=decimal.Decimal("0.00"),
                gst=decimal.Decimal("0.00"),
                total=decimal.Decimal("0.00"),
                payment_status="Paid"
            )

            generate_invoice_pdf(invoice)

            # Redeem atomic
            redeem_promo_atomic(
                promo_code=promo,
                user=request.user,
                subscription=subscription,
                payment=payment,
                invoice=invoice,
                ip_address=ip_address,
                user_agent=user_agent
            )

            subscription.update_status()
            clear_subscription_cache(request)

            # Clear session promo
            request.session.pop("applied_promo_code", None)
            request.session.pop("applied_promo_subscription_id", None)

        return JsonResponse({
            "status": "ok",
            "message": "Free subscription activated successfully!",
            "redirect_url": "/en/payments/payment-succeed/"
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Free activation failed: {str(e)}"}, status=500)
