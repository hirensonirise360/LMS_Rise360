import os
import uuid
import json
import decimal
import razorpay
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.db import models, transaction

from accounts.models import User
from .models import Subscription, Payment, Invoice, PromoCode, PromoRedemption
from .promo_service import (
    validate_promo_code,
    calculate_promo_effect,
    redeem_promo_atomic,
    get_auto_apply_promo
)
from .utils import generate_invoice_pdf
from .middleware import clear_subscription_cache

# Helper to check authorized admin
def is_authorized_admin(user):
    return user.is_active and user.is_superuser and user.email == "sonihiren233@gmail.com"

# Initialize Razorpay Client
try:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception as e:
    razorpay_client = None


@login_required
def billing(request):
    """
    Billing feature has been removed. Redirects to main student dashboard.
    """
    return redirect("ea_home")


@login_required
def billing_checkout(request, subscription_id=None):
    """
    Pricing/Checkout screen showing Razorpay, UPI QR options, and Promo Code section.
    """
    subscription = None
    if subscription_id:
        subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    else:
        subscription = Subscription.objects.filter(user=request.user, status="Pending").first()
        if not subscription:
            subscription = Subscription.objects.create(
                user=request.user,
                plan="Lifetime",
                amount=decimal.Decimal("4999.00"),
                original_amount=decimal.Decimal("4999.00"),
                lifetime=True,
                status="Pending",
                payment_status="Pending"
            )

    if subscription.status == "Active":
        messages.info(request, "You already have an active subscription.")
        return redirect("billing")

    if not subscription.original_amount:
        subscription.original_amount = subscription.amount
        subscription.save(update_fields=["original_amount"])

    orig_amount = subscription.original_amount

    # Promo session check or auto-apply check
    applied_code = request.session.get("applied_promo_code")
    applied_promo = None
    if applied_code:
        val_res = validate_promo_code(applied_code, request.user, subscription.plan, orig_amount)
        if val_res["valid"]:
            applied_promo = val_res["promo"]
        else:
            request.session.pop("applied_promo_code", None)

    if not applied_promo:
        auto_promo = get_auto_apply_promo(request.user, subscription.plan, orig_amount)
        if auto_promo:
            applied_promo = auto_promo
            request.session["applied_promo_code"] = auto_promo.code

    calc = calculate_promo_effect(applied_promo, orig_amount)
    final_amount = calc["final_amount"]

    # Save promo calculation on subscription
    subscription.amount = final_amount
    subscription.discount_amount = calc["discount_amount"]
    subscription.applied_promo = applied_promo
    subscription.save(update_fields=["amount", "discount_amount", "applied_promo", "updated_at"])

    # Fetch active public promos to display for copy/apply
    public_promos = PromoCode.objects.filter(
        is_active=True,
        is_public=True,
        is_archived=False
    ).filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=timezone.now())
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
    ).order_by("-priority")[:4]

    import urllib.parse
    upi_link = f"upi://pay?pa=sonih4495@ybl&pn=RISE360%20Institute&am={int(final_amount)}&cu=INR"
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(upi_link)}"

    context = {
        "title": "Activate Subscription",
        "subscription": subscription,
        "upi_id": "sonih4495@ybl",
        "upi_link": upi_link,
        "qr_code_url": qr_code_url,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "applied_promo": applied_promo,
        "original_amount": calc["original_amount"],
        "discount_amount": calc["discount_amount"],
        "final_amount": calc["final_amount"],
        "extra_days": calc["extra_days"],
        "is_free": calc["is_free"],
        "promo_summary": calc["summary"],
        "public_promos": public_promos,
    }
    return render(request, "payments/checkout.html", context)


@login_required
@require_POST
def change_plan_checkout(request, subscription_id):
    """
    AJAX or Post view to change the plan of a pending subscription.
    """
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    if subscription.status == "Active":
        return JsonResponse({"status": "error", "message": "Cannot change plan of an active subscription."}, status=400)

    plan = request.POST.get("plan")
    plan_amounts = {
        "Yearly": decimal.Decimal("2999.00"),
        "Lifetime": decimal.Decimal("4999.00")
    }

    if plan not in plan_amounts:
        return JsonResponse({"status": "error", "message": "The selected plan is unavailable or no longer offered."}, status=400)

    orig_amount = plan_amounts[plan]
    subscription.plan = plan
    subscription.original_amount = orig_amount
    subscription.lifetime = (plan == "Lifetime")

    applied_code = request.session.get("applied_promo_code")
    applied_promo = None
    if applied_code:
        val_res = validate_promo_code(applied_code, request.user, plan, orig_amount)
        if val_res["valid"]:
            applied_promo = val_res["promo"]

    calc = calculate_promo_effect(applied_promo, orig_amount)
    subscription.amount = calc["final_amount"]
    subscription.discount_amount = calc["discount_amount"]
    subscription.applied_promo = applied_promo
    subscription.save()

    return JsonResponse({
        "status": "ok",
        "original_amount": str(calc["original_amount"]),
        "discount_amount": str(calc["discount_amount"]),
        "amount": str(calc["final_amount"]),
        "plan": subscription.plan,
        "lifetime": subscription.lifetime,
        "extra_days": calc["extra_days"],
        "is_free": calc["is_free"],
        "summary": calc["summary"]
    })


@login_required
@require_POST
def razorpay_create_order(request):
    """
    API view to create a Razorpay order for the selected subscription (using promo discounted amount).
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    subscription_id = data.get("subscription_id")
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if not razorpay_client:
        return JsonResponse({
            "status": "error",
            "message": "Razorpay client is not configured correctly."
        }, status=500)

    orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount
    applied_code = request.session.get("applied_promo_code") or (subscription.applied_promo.code if subscription.applied_promo else None)

    applied_promo = None
    if applied_code:
        val_res = validate_promo_code(applied_code, request.user, subscription.plan, orig_amount)
        if val_res["valid"]:
            applied_promo = val_res["promo"]

    calc = calculate_promo_effect(applied_promo, orig_amount)
    final_amount = calc["final_amount"]

    subscription.amount = final_amount
    subscription.discount_amount = calc["discount_amount"]
    subscription.applied_promo = applied_promo
    subscription.save(update_fields=["amount", "discount_amount", "applied_promo", "updated_at"])

    # Razorpay amount in paise
    amount_paise = int(final_amount * 100)

    try:
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"receipt_{subscription.id}_{int(timezone.now().timestamp())}",
            "payment_capture": 1
        }
        razorpay_order = razorpay_client.order.create(data=order_data)

        # Save order ID in pending payment record
        Payment.objects.create(
            subscription=subscription,
            user=request.user,
            amount=final_amount,
            discount_amount=calc["discount_amount"],
            promo_code=applied_promo,
            gateway="Razorpay",
            order_id=razorpay_order["id"],
            status="Pending"
        )

        return JsonResponse({
            "status": "ok",
            "order_id": razorpay_order["id"],
            "amount": amount_paise,
            "key": settings.RAZORPAY_KEY_ID
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": f"Failed to create order: {str(e)}"
        }, status=500)


@login_required
@require_POST
def razorpay_verify_payment(request):
    """
    API view to verify Razorpay signature and activate subscription with promo redemption.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    payment_id = data.get("razorpay_payment_id")
    order_id = data.get("razorpay_order_id")
    signature = data.get("razorpay_signature")
    subscription_id = data.get("subscription_id")

    if not razorpay_client:
        return JsonResponse({"status": "error", "message": "Razorpay is not configured."}, status=500)

    params = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature
    }

    try:
        razorpay_client.utility.verify_payment_signature(params)
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({"status": "error", "message": "Signature verification failed. Potential tampering detected."}, status=400)

    ip_address = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    try:
        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(id=subscription_id, user=request.user)

            # Re-evaluate applied promo
            orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount
            applied_code = request.session.get("applied_promo_code") or (subscription.applied_promo.code if subscription.applied_promo else None)

            applied_promo = None
            if applied_code:
                val_res = validate_promo_code(applied_code, request.user, subscription.plan, orig_amount)
                if val_res["valid"]:
                    applied_promo = val_res["promo"]

            calc = calculate_promo_effect(applied_promo, orig_amount)
            final_amount = calc["final_amount"]

            payment = Payment.objects.filter(order_id=order_id).first()
            if not payment:
                payment = Payment.objects.create(
                    subscription=subscription,
                    user=request.user,
                    amount=final_amount,
                    discount_amount=calc["discount_amount"],
                    promo_code=applied_promo,
                    gateway="Razorpay",
                    order_id=order_id,
                )

            payment.razorpay_payment_id = payment_id
            payment.signature = signature
            payment.status = "Success"
            payment.save()

            # Deactivate active ones
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
            subscription.payment_mode = "Razorpay"
            subscription.transaction_id = payment_id
            subscription.original_amount = orig_amount
            subscription.amount = final_amount
            subscription.discount_amount = calc["discount_amount"]
            subscription.applied_promo = applied_promo

            invoice_id = str(uuid.uuid4())[:8].upper()
            invoice_num = f"RISE360-INV-{now.strftime('%Y%m%d')}-{invoice_id}"
            subscription.invoice_number = invoice_num
            subscription.status = "Active"
            subscription.save()

            # Create Invoice
            invoice = Invoice.objects.create(
                invoice_number=invoice_num,
                user=request.user,
                subscription=subscription,
                original_amount=orig_amount,
                discount_amount=calc["discount_amount"],
                promo_code_str=applied_promo.code if applied_promo else None,
                amount=final_amount,
                gst=decimal.Decimal("0.00"),
                total=final_amount,
                payment_status="Paid"
            )

            generate_invoice_pdf(invoice)

            # Atomic redemption
            if applied_promo:
                redeem_promo_atomic(
                    promo_code=applied_promo,
                    user=request.user,
                    subscription=subscription,
                    payment=payment,
                    invoice=invoice,
                    ip_address=ip_address,
                    user_agent=user_agent
                )

            subscription.update_status()
            clear_subscription_cache(request)

            request.session.pop("applied_promo_code", None)
            request.session.pop("applied_promo_subscription_id", None)

        messages.success(request, "Payment verified! Your subscription is now active.")
        return JsonResponse({"status": "ok", "redirect_url": "/en/payments/payment-succeed/"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Activation failed: {str(e)}"}, status=500)


@login_required
@require_POST
def qr_submit_verification(request, subscription_id):
    """
    Processes the submission of manual UPI QR payment proof.
    """
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    utr_number = request.POST.get("utr_number", "").strip()
    screenshot = request.FILES.get("screenshot")

    if not utr_number or not screenshot:
        messages.error(request, "Transaction UTR number and Screenshot are required.")
        return redirect("billing_checkout", subscription_id=subscription.id)

    duplicate = Payment.objects.filter(utr_number=utr_number).exists()
    if duplicate:
        messages.error(request, "This Transaction Reference Number (UTR) has already been submitted.")
        return redirect("billing_checkout", subscription_id=subscription.id)

    orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount
    applied_code = request.session.get("applied_promo_code") or (subscription.applied_promo.code if subscription.applied_promo else None)

    applied_promo = None
    if applied_code:
        val_res = validate_promo_code(applied_code, request.user, subscription.plan, orig_amount)
        if val_res["valid"]:
            applied_promo = val_res["promo"]

    calc = calculate_promo_effect(applied_promo, orig_amount)
    final_amount = calc["final_amount"]

    payment = Payment.objects.create(
        subscription=subscription,
        user=request.user,
        amount=final_amount,
        discount_amount=calc["discount_amount"],
        promo_code=applied_promo,
        gateway="QR Code",
        utr_number=utr_number,
        screenshot=screenshot,
        status="Pending"
    )

    subscription.amount = final_amount
    subscription.discount_amount = calc["discount_amount"]
    subscription.applied_promo = applied_promo
    subscription.payment_status = "Pending"
    subscription.status = "Pending"
    subscription.save()

    messages.info(request, "Your payment proof has been submitted. Our team is verifying your payment UTR.")
    return redirect("billing")


@login_required
def download_invoice(request, invoice_id):
    """
    Serves the generated PDF file of the invoice.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if invoice.user != request.user and not request.user.is_superuser:
        messages.error(request, "Permission denied.")
        return redirect("billing")

    if not invoice.pdf_path:
        generate_invoice_pdf(invoice)

    from django.core.files.storage import default_storage
    filepath = invoice.pdf_path

    if not default_storage.exists(filepath):
        generate_invoice_pdf(invoice)

    try:
        with default_storage.open(filepath) as pdf:
            response = HttpResponse(pdf.read(), content_type="application/pdf")
            response["Content-Disposition"] = f"inline; filename={os.path.basename(filepath)}"
            return response
    except Exception as e:
        messages.error(request, f"Could not load PDF: {e}")
        return redirect("billing")


@login_required
def payment_success(request):
    return render(request, "payments/payment_success.html", {"title": "Payment Successful"})


@login_required
def payment_failed(request):
    reason = request.GET.get("reason", "An unknown error occurred during Razorpay validation.")
    return render(request, "payments/payment_failed.html", {"title": "Payment Failed", "reason": reason})


@login_required
def subscription_required(request):
    return redirect("ea_home")


@login_required
def subscription_expired(request):
    return redirect("ea_home")


# ==============================================================================
# CUSTOM SUPERUSER ADMIN SUBSCRIPTION DASHBOARD
# ==============================================================================

@user_passes_test(is_authorized_admin)
def admin_subscription_dashboard(request):
    status_filter = request.GET.get("status", "")
    plan_filter = request.GET.get("plan", "")
    pay_filter = request.GET.get("payment", "")
    search_query = request.GET.get("search", "")

    today = timezone.now().date()
    seven_days_later = today + timezone.timedelta(days=7)

    # 1. Compute all subscription KPI metrics in a SINGLE database query via conditional aggregation
    sub_metrics = Subscription.objects.aggregate(
        total_subscribers=models.Count("id", filter=models.Q(status="Active")),
        monthly_subscribers=models.Count("id", filter=models.Q(status="Active", plan="Monthly")),
        lifetime_subscribers=models.Count("id", filter=models.Q(status="Active", plan="Lifetime")),
        expired_users=models.Count("id", filter=models.Q(status="Expired")),
        upcoming_expiries=models.Count("id", filter=models.Q(
            status="Active",
            lifetime=False,
            end_date__date__range=[today, seven_days_later]
        ))
    )

    total_subscribers = sub_metrics["total_subscribers"] or 0
    monthly_subscribers = sub_metrics["monthly_subscribers"] or 0
    lifetime_subscribers = sub_metrics["lifetime_subscribers"] or 0
    expired_users = sub_metrics["expired_users"] or 0
    upcoming_expiries = sub_metrics["upcoming_expiries"] or 0

    pending_verifications = Payment.objects.filter(status="Pending", gateway="QR Code").count()

    # 2. Compute total revenue directly in PostgreSQL database engine (0ms latency)
    rev_agg = Invoice.objects.filter(payment_status="Paid").aggregate(total_rev=models.Sum("total"))
    total_revenue = rev_agg["total_rev"] or decimal.Decimal("0.00")

    # 3. Optimize queryset with select_related to eliminate N+1 queries in template loop
    subscriptions = Subscription.objects.select_related("user", "applied_promo").all()

    if search_query:
        subscriptions = subscriptions.filter(
            models.Q(user__email__icontains=search_query) |
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(utr_number__icontains=search_query) |
            models.Q(transaction_id__icontains=search_query) |
            models.Q(invoice_number__icontains=search_query)
        )

    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    if plan_filter:
        subscriptions = subscriptions.filter(plan=plan_filter)
    if pay_filter:
        subscriptions = subscriptions.filter(payment_status=pay_filter)

    pending_qr_list = Payment.objects.filter(status="Pending", gateway="QR Code").select_related(
        "user", "subscription", "subscription__user", "promo_code"
    )

    context = {
        "title": "Subscription Dashboard",
        "subscriptions": subscriptions[:100],
        "pending_qr_list": pending_qr_list,
        "total_subscribers": total_subscribers,
        "monthly_subscribers": monthly_subscribers,
        "lifetime_subscribers": lifetime_subscribers,
        "expired_users": expired_users,
        "pending_verifications": pending_verifications,
        "total_revenue": total_revenue,
        "upcoming_expiries": upcoming_expiries,
        "search_query": search_query,
        "status_filter": status_filter,
        "plan_filter": plan_filter,
        "pay_filter": pay_filter,
    }
    return render(request, "payments/admin_dashboard.html", context)


@user_passes_test(is_authorized_admin)
def admin_subscription_search_api(request):
    """
    Fast JSON API endpoint for debounced live search and dynamic filtering.
    """
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()
    plan_filter = request.GET.get("plan", "").strip()
    pay_filter = request.GET.get("payment", "").strip()

    subscriptions = Subscription.objects.select_related("user", "applied_promo").all()

    if search_query:
        subscriptions = subscriptions.filter(
            models.Q(user__email__icontains=search_query) |
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(utr_number__icontains=search_query) |
            models.Q(transaction_id__icontains=search_query) |
            models.Q(invoice_number__icontains=search_query)
        )

    if status_filter:
        subscriptions = subscriptions.filter(status=status_filter)
    if plan_filter:
        subscriptions = subscriptions.filter(plan=plan_filter)
    if pay_filter:
        subscriptions = subscriptions.filter(payment_status=pay_filter)

    sub_list = []
    for sub in subscriptions[:100]:
        sub_list.append({
            "id": sub.id,
            "user_name": sub.user.get_full_name() or sub.user.email,
            "user_email": sub.user.email,
            "plan": sub.plan,
            "payment_mode": sub.payment_mode or "N/A",
            "amount": str(sub.amount),
            "status": sub.status,
            "lifetime": sub.lifetime,
            "remaining_days": sub.remaining_days or 0,
            "start_date": sub.start_date.strftime("%Y-%m-%d") if sub.start_date else "N/A",
            "end_date": sub.end_date.strftime("%Y-%m-%d") if sub.end_date else "N/A",
            "invoice_number": sub.invoice_number or "-",
            "transaction_id": sub.transaction_id or "-",
        })

    return JsonResponse({"success": True, "count": len(sub_list), "subscriptions": sub_list})



@user_passes_test(is_authorized_admin)
@require_POST
def admin_approve_qr(request, payment_id):
    """
    Approves a pending QR payment and activates the user's subscription with promo redemption.
    """
    payment = get_object_or_404(Payment, id=payment_id, status="Pending", gateway="QR Code")
    subscription = payment.subscription

    try:
        with transaction.atomic():
            payment.status = "Success"
            payment.save()

            Subscription.objects.filter(user=payment.user, status="Active").update(status="Cancelled")

            orig_amount = subscription.original_amount if subscription.original_amount else subscription.amount
            promo = payment.promo_code or subscription.applied_promo
            calc = calculate_promo_effect(promo, orig_amount)
            final_amount = calc["final_amount"]

            now = timezone.now()
            subscription.start_date = now
            if subscription.plan == "Monthly":
                subscription.end_date = now + timezone.timedelta(days=30)
            elif subscription.plan == "Yearly":
                subscription.end_date = now + timezone.timedelta(days=365)
            else:
                subscription.end_date = None

            subscription.payment_status = "Paid"
            subscription.payment_mode = "QR Code"
            subscription.transaction_id = payment.utr_number
            subscription.original_amount = orig_amount
            subscription.amount = final_amount
            subscription.discount_amount = calc["discount_amount"]
            subscription.applied_promo = promo

            invoice_id = str(uuid.uuid4())[:8].upper()
            invoice_num = f"RISE360-INV-{now.strftime('%Y%m%d')}-{invoice_id}"
            subscription.invoice_number = invoice_num
            subscription.status = "Active"
            subscription.save()

            try:
                clear_subscription_cache(request)
            except Exception:
                pass

            invoice = Invoice.objects.create(
                invoice_number=invoice_num,
                user=payment.user,
                subscription=subscription,
                original_amount=orig_amount,
                discount_amount=calc["discount_amount"],
                promo_code_str=promo.code if promo else None,
                amount=final_amount,
                gst=decimal.Decimal("0.00"),
                total=final_amount,
                payment_status="Paid"
            )
            generate_invoice_pdf(invoice)

            if promo:
                redeem_promo_atomic(
                    promo_code=promo,
                    user=payment.user,
                    subscription=subscription,
                    payment=payment,
                    invoice=invoice
                )

            subscription.update_status()

        messages.success(request, f"Approved UTR {payment.utr_number}. User {payment.user.email} subscription is now active.")
    except Exception as e:
        messages.error(request, f"Failed to approve QR payment: {e}")

    return redirect("admin_subscription_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_reject_qr(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, status="Pending", gateway="QR Code")
    subscription = payment.subscription

    payment.status = "Failed"
    payment.save()

    subscription.status = "Cancelled"
    subscription.payment_status = "Failed"
    subscription.save()

    messages.warning(request, f"Rejected UTR {payment.utr_number}. Subscription cancelled.")
    return redirect("admin_subscription_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_extend_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id, status="Active", lifetime=False)

    if not subscription.end_date:
        subscription.end_date = timezone.now()

    subscription.end_date = subscription.end_date + timezone.timedelta(days=30)
    subscription.save()
    subscription.update_status()

    messages.success(request, f"Extended subscription for {subscription.user.email} by 30 days. New expiry: {subscription.end_date.strftime('%Y-%m-%d')}")
    return redirect("admin_subscription_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_convert_lifetime(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    subscription.plan = "Lifetime"
    subscription.lifetime = True
    subscription.end_date = None
    subscription.status = "Active"
    subscription.save()
    subscription.update_status()

    messages.success(request, f"Converted subscription for {subscription.user.email} to Lifetime.")
    return redirect("admin_subscription_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_cancel_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)
    subscription.status = "Cancelled"
    subscription.save()
    subscription.update_status()

    messages.warning(request, f"Cancelled subscription for {subscription.user.email}.")
    return redirect("admin_subscription_dashboard")
