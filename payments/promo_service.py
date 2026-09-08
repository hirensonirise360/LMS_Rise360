import decimal
from django.db import transaction
from django.utils import timezone
from .models import PromoCode, PromoRedemption, PromoAuditLog, Subscription, Payment, Invoice


def validate_promo_code(code_str, user, plan, original_amount):
    """
    Validates a promo code against all database rules and constraints.
    Returns dict: {"valid": bool, "error": str or None, "promo": PromoCode or None}
    """
    if not code_str or not str(code_str).strip():
        return {"valid": False, "error": "Please enter a promo code.", "promo": None}

    clean_code = str(code_str).strip().upper()
    promo = PromoCode.objects.filter(code__iexact=clean_code, is_archived=False).first()

    if not promo:
        return {"valid": False, "error": "Invalid promo code.", "promo": None}

    if not promo.is_active:
        return {"valid": False, "error": "This promo code is currently inactive.", "promo": promo}

    now = timezone.now()

    if promo.start_date and now < promo.start_date:
        return {"valid": False, "error": "This promo code is not active yet.", "promo": promo}

    if promo.end_date and now > promo.end_date:
        return {"valid": False, "error": "This promo code has expired.", "promo": promo}

    # Global Usage Limit
    if promo.overall_usage_limit and promo.overall_usage_count >= promo.overall_usage_limit:
        return {"valid": False, "error": "This promo code has reached its maximum usage limit.", "promo": promo}

    # Per User Limit
    if user and user.is_authenticated:
        user_redemptions = PromoRedemption.objects.filter(
            promo_code=promo,
            user=user,
            status__in=["redeemed", "applied"]
        ).count()
        if promo.per_user_limit and user_redemptions >= promo.per_user_limit:
            return {"valid": False, "error": f"You have already reached the maximum usage limit ({promo.per_user_limit}) for this promo code.", "promo": promo}

        # First Purchase Only
        paid_subs = Subscription.objects.filter(user=user, payment_status="Paid").count()
        if promo.first_purchase_only and paid_subs > 0:
            return {"valid": False, "error": "This promo code is valid for first-time purchases only.", "promo": promo}

        # Existing Users Only
        if promo.existing_users_only and paid_subs == 0:
            return {"valid": False, "error": "This promo code is valid for existing subscribers only.", "promo": promo}

        # User Specific Restrictions
        if promo.allowed_users.exists() and not promo.allowed_users.filter(id=user.id).exists():
            return {"valid": False, "error": "You are not eligible to use this promo code.", "promo": promo}

        # Email Specific Restrictions
        if promo.allowed_emails and promo.allowed_emails.strip():
            user_email = user.email.strip().lower()
            allowed_list = [e.strip().lower() for e in promo.allowed_emails.replace('\n', ',').split(',') if e.strip()]
            email_matched = False
            for pattern in allowed_list:
                if pattern.startswith('@'):
                    if user_email.endswith(pattern):
                        email_matched = True
                        break
                elif user_email == pattern:
                    email_matched = True
                    break
            if not email_matched:
                return {"valid": False, "error": "Your email address is not eligible for this promo code.", "promo": promo}

    # Plan Restrictions
    if plan and promo.allowed_plans and len(promo.allowed_plans) > 0:
        if plan not in promo.allowed_plans:
            allowed_str = ", ".join(promo.allowed_plans)
            return {"valid": False, "error": f"This promo code is only valid for the following plans: {allowed_str}.", "promo": promo}

    # Minimum Purchase Amount
    orig_dec = decimal.Decimal(str(original_amount))
    if promo.min_purchase_amount and orig_dec < promo.min_purchase_amount:
        return {"valid": False, "error": f"Minimum purchase amount of ₹{promo.min_purchase_amount} required to use this promo code.", "promo": promo}

    # Maximum Purchase Amount
    if promo.max_purchase_amount and orig_dec > promo.max_purchase_amount:
        return {"valid": False, "error": f"This promo code is only valid for purchases up to ₹{promo.max_purchase_amount}.", "promo": promo}

    return {"valid": True, "error": None, "promo": promo}


def calculate_promo_effect(promo, original_amount):
    """
    Computes original amount, discount, final payable amount, extra validity days, and free status.
    """
    orig = decimal.Decimal(str(original_amount))
    if not promo:
        return {
            "original_amount": orig,
            "discount_amount": decimal.Decimal("0.00"),
            "final_amount": orig,
            "extra_days": 0,
            "is_free": False,
            "summary": "No promo applied."
        }

    discount = promo.calculate_discount(orig)
    final_amt = max(decimal.Decimal("0.00"), orig - discount)
    extra_days = promo.total_extra_days
    is_free = (final_amt == decimal.Decimal("0.00"))

    summary_parts = []
    if discount > 0:
        summary_parts.append(f"₹{discount} Discount")
    if extra_days > 0:
        summary_parts.append(f"+{extra_days} Extra Days")
    if not summary_parts:
        summary_parts.append("Promo applied")

    return {
        "original_amount": orig,
        "discount_amount": discount,
        "final_amount": final_amt,
        "extra_days": extra_days,
        "is_free": is_free,
        "summary": " & ".join(summary_parts)
    }


def get_auto_apply_promo(user, plan, original_amount):
    """
    Finds the highest priority eligible auto-apply promo code.
    """
    auto_promos = PromoCode.objects.filter(
        is_active=True,
        is_archived=False,
        auto_apply=True
    ).order_by("-priority", "-discount_value")

    for promo in auto_promos:
        val_res = validate_promo_code(promo.code, user, plan, original_amount)
        if val_res["valid"]:
            return promo
    return None


def redeem_promo_atomic(promo_code, user, subscription, payment=None, invoice=None, ip_address=None, user_agent=""):
    """
    Atomically redeems a promo code, updates counters, applies extra validity to subscription,
    and logs the redemption record.
    """
    if not promo_code:
        return None

    with transaction.atomic():
        promo = PromoCode.objects.select_for_update().get(id=promo_code.id)

        # Final check inside lock
        if promo.overall_usage_limit and promo.overall_usage_count >= promo.overall_usage_limit:
            raise ValueError("Promo code global usage limit was reached during transaction.")

        promo.overall_usage_count += 1
        promo.save(update_fields=["overall_usage_count", "updated_at"])

        orig_amt = subscription.original_amount if subscription.original_amount else subscription.amount
        calc = calculate_promo_effect(promo, orig_amt)

        extra_days = calc["extra_days"]
        if extra_days > 0 and subscription.end_date and not subscription.lifetime:
            subscription.end_date += timezone.timedelta(days=extra_days)
            subscription.extra_days_granted = (subscription.extra_days_granted or 0) + extra_days
            subscription.save(update_fields=["end_date", "extra_days_granted", "updated_at"])

        subscription.applied_promo = promo
        subscription.discount_amount = calc["discount_amount"]
        subscription.amount = calc["final_amount"]
        subscription.save(update_fields=["applied_promo", "discount_amount", "amount", "updated_at"])

        redemption = PromoRedemption.objects.create(
            promo_code=promo,
            user=user,
            subscription=subscription,
            payment=payment,
            invoice=invoice,
            original_amount=calc["original_amount"],
            discount_amount=calc["discount_amount"],
            final_amount=calc["final_amount"],
            extra_days_granted=extra_days,
            status="redeemed",
            ip_address=ip_address,
            user_agent=user_agent
        )

        log_promo_action(
            promo_code=promo,
            action="REDEEMED",
            performed_by=user,
            changes={
                "user": user.email,
                "subscription_id": subscription.id,
                "discount_amount": str(calc["discount_amount"]),
                "final_amount": str(calc["final_amount"]),
                "extra_days": extra_days
            }
        )

        return redemption


def log_promo_action(promo_code, action, performed_by=None, changes=None):
    """
    Utility to record an administrative or system audit log entry for a promo code.
    """
    code_str = promo_code.code if promo_code else "SYSTEM"
    PromoAuditLog.objects.create(
        promo_code=promo_code,
        code_str=code_str,
        action=action,
        performed_by=performed_by,
        changes=changes or {}
    )
