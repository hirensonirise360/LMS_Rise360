import csv
import json
import decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import models

from accounts.models import User
from .models import PromoCode, PromoRedemption, PromoAuditLog, Subscription
from .promo_service import log_promo_action


def is_authorized_admin(user):
    return user.is_active and user.is_superuser and user.email == "sonihiren233@gmail.com"


@user_passes_test(is_authorized_admin)
def admin_promo_dashboard(request):
    """
    Main Admin Dashboard & List view for Promo Code / Coupon Management.
    Includes analytics, metrics, search, filter, sorting, and top performer stats.
    """
    status_filter = request.GET.get("status", "")
    type_filter = request.GET.get("type", "")
    visibility_filter = request.GET.get("visibility", "")
    search_query = request.GET.get("search", "")
    sort_by = request.GET.get("sort", "-created_at")

    all_promos = PromoCode.objects.all()
    now = timezone.now()

    # Calculate overall dashboard metrics via database aggregation (0ms latency)
    unarchived_promos = all_promos.filter(is_archived=False)
    total_promos_count = unarchived_promos.count()

    promo_metrics = unarchived_promos.aggregate(
        active_count=models.Count("id", filter=models.Q(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ) | models.Q(
            is_active=True,
            start_date__isnull=True,
            end_date__isnull=True
        )),
        expired_count=models.Count("id", filter=models.Q(end_date__lt=now)),
        upcoming_count=models.Count("id", filter=models.Q(start_date__gt=now)),
        inactive_count=models.Count("id", filter=models.Q(is_active=False))
    )

    active_count = promo_metrics["active_count"] or 0
    expired_count = promo_metrics["expired_count"] or 0
    upcoming_count = promo_metrics["upcoming_count"] or 0
    inactive_count = promo_metrics["inactive_count"] or 0

    redemption_stats = PromoRedemption.objects.filter(status="redeemed").aggregate(
        total_count=models.Count("id"),
        total_discount=models.Sum("discount_amount"),
        total_revenue=models.Sum("final_amount")
    )
    total_redemptions_count = redemption_stats["total_count"] or 0
    total_discount_given = redemption_stats["total_discount"] or decimal.Decimal("0.00")
    total_revenue_generated = redemption_stats["total_revenue"] or decimal.Decimal("0.00")

    # Top performing promos by redemption count
    top_promos = PromoCode.objects.filter(is_archived=False).order_by("-overall_usage_count")[:5]

    # Filter promo list
    qs = all_promos
    if status_filter:
        if status_filter == "Archived":
            qs = qs.filter(is_archived=True)
        elif status_filter == "Inactive":
            qs = qs.filter(is_active=False, is_archived=False)
        elif status_filter == "Active":
            qs = qs.filter(
                is_active=True,
                is_archived=False
            ).filter(
                models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
            ).filter(
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
            )
        elif status_filter == "Expired":
            qs = qs.filter(end_date__lt=now, is_archived=False)
        elif status_filter == "Upcoming":
            qs = qs.filter(start_date__gt=now, is_archived=False)
    else:
        qs = qs.filter(is_archived=False)

    if type_filter:
        qs = qs.filter(discount_type=type_filter)
    if visibility_filter:
        if visibility_filter == "public":
            qs = qs.filter(is_public=True)
        elif visibility_filter == "private":
            qs = qs.filter(is_public=False)

    if search_query:
        qs = qs.filter(
            models.Q(code__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(admin_notes__icontains=search_query)
        )

    # Sort
    valid_sorts = ["code", "-code", "created_at", "-created_at", "priority", "-priority", "overall_usage_count", "-overall_usage_count", "end_date", "-end_date"]
    if sort_by in valid_sorts:
        qs = qs.order_by(sort_by)
    else:
        qs = qs.order_by("-created_at")

    # Recent redemptions
    recent_redemptions = PromoRedemption.objects.select_related("promo_code", "user", "subscription").order_by("-redeemed_at")[:10]

    context = {
        "title": "Promo & Coupon Management",
        "promos": qs,
        "total_promos_count": total_promos_count,
        "active_count": active_count,
        "expired_count": expired_count,
        "upcoming_count": upcoming_count,
        "inactive_count": inactive_count,
        "total_redemptions_count": total_redemptions_count,
        "total_discount_given": total_discount_given,
        "total_revenue_generated": total_revenue_generated,
        "top_promos": top_promos,
        "recent_redemptions": recent_redemptions,
        "search_query": search_query,
        "status_filter": status_filter,
        "type_filter": type_filter,
        "visibility_filter": visibility_filter,
        "sort_by": sort_by,
    }
    return render(request, "payments/admin_promos_dashboard.html", context)


@user_passes_test(is_authorized_admin)
def admin_promo_create(request):
    """
    Form view to create a new Promo Code with complete rule definitions.
    """
    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        description = request.POST.get("description", "").strip()
        admin_notes = request.POST.get("admin_notes", "").strip()
        discount_type = request.POST.get("discount_type", "fixed")
        discount_value_str = request.POST.get("discount_value", "0.00")
        max_discount_str = request.POST.get("max_discount_amount", "")

        extra_days = int(request.POST.get("extra_validity_days", 0) or 0)
        extra_months = int(request.POST.get("extra_validity_months", 0) or 0)
        extra_years = int(request.POST.get("extra_validity_years", 0) or 0)

        is_active = request.POST.get("is_active") == "on"
        is_public = request.POST.get("is_public") == "on"
        auto_apply = request.POST.get("auto_apply") == "on"
        stackable = request.POST.get("stackable") == "on"
        priority = int(request.POST.get("priority", 0) or 0)

        start_date_str = request.POST.get("start_date", "").strip()
        end_date_str = request.POST.get("end_date", "").strip()

        min_purchase_str = request.POST.get("min_purchase_amount", "0.00")
        max_purchase_str = request.POST.get("max_purchase_amount", "")

        overall_limit_str = request.POST.get("overall_usage_limit", "")
        per_user_limit = int(request.POST.get("per_user_limit", 1) or 1)

        first_purchase_only = request.POST.get("first_purchase_only") == "on"
        existing_users_only = request.POST.get("existing_users_only") == "on"

        allowed_plans = request.POST.getlist("allowed_plans")
        allowed_emails = request.POST.get("allowed_emails", "").strip()

        if not code:
            messages.error(request, "Promo code string is required.")
            return render(request, "payments/admin_promo_form.html", {"title": "Create Promo Code", "action": "create"})

        if PromoCode.objects.filter(code__iexact=code).exists():
            messages.error(request, f"A promo code with the code '{code}' already exists.")
            return render(request, "payments/admin_promo_form.html", {"title": "Create Promo Code", "action": "create"})

        disc_val = decimal.Decimal(discount_value_str or "0.00")
        max_disc = decimal.Decimal(max_discount_str) if max_discount_str else None
        min_purch = decimal.Decimal(min_purchase_str or "0.00")
        max_purch = decimal.Decimal(max_purchase_str) if max_purchase_str else None
        overall_limit = int(overall_limit_str) if overall_limit_str else None

        start_date = timezone.datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = timezone.datetime.fromisoformat(end_date_str) if end_date_str else None

        promo = PromoCode.objects.create(
            code=code,
            description=description,
            admin_notes=admin_notes,
            discount_type=discount_type,
            discount_value=disc_val,
            max_discount_amount=max_disc,
            extra_validity_days=extra_days,
            extra_validity_months=extra_months,
            extra_validity_years=extra_years,
            is_active=is_active,
            is_public=is_public,
            auto_apply=auto_apply,
            stackable=stackable,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            min_purchase_amount=min_purch,
            max_purchase_amount=max_purch,
            overall_usage_limit=overall_limit,
            per_user_limit=per_user_limit,
            first_purchase_only=first_purchase_only,
            existing_users_only=existing_users_only,
            allowed_plans=allowed_plans,
            allowed_emails=allowed_emails,
            created_by=request.user
        )

        log_promo_action(promo, "CREATED", request.user, {"code": promo.code, "discount_type": discount_type})
        messages.success(request, f"Promo Code '{promo.code}' created successfully!")
        return redirect("admin_promo_dashboard")

    context = {
        "title": "Create Promo Code",
        "action": "create",
        "all_plans": ["Monthly", "Yearly", "Lifetime"]
    }
    return render(request, "payments/admin_promo_form.html", context)


@user_passes_test(is_authorized_admin)
def admin_promo_edit(request, promo_id):
    """
    Form view to update an existing Promo Code.
    """
    promo = get_object_or_404(PromoCode, id=promo_id)

    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()
        description = request.POST.get("description", "").strip()
        admin_notes = request.POST.get("admin_notes", "").strip()
        discount_type = request.POST.get("discount_type", "fixed")
        discount_value_str = request.POST.get("discount_value", "0.00")
        max_discount_str = request.POST.get("max_discount_amount", "")

        extra_days = int(request.POST.get("extra_validity_days", 0) or 0)
        extra_months = int(request.POST.get("extra_validity_months", 0) or 0)
        extra_years = int(request.POST.get("extra_validity_years", 0) or 0)

        is_active = request.POST.get("is_active") == "on"
        is_public = request.POST.get("is_public") == "on"
        auto_apply = request.POST.get("auto_apply") == "on"
        stackable = request.POST.get("stackable") == "on"
        priority = int(request.POST.get("priority", 0) or 0)

        start_date_str = request.POST.get("start_date", "").strip()
        end_date_str = request.POST.get("end_date", "").strip()

        min_purchase_str = request.POST.get("min_purchase_amount", "0.00")
        max_purchase_str = request.POST.get("max_purchase_amount", "")

        overall_limit_str = request.POST.get("overall_usage_limit", "")
        per_user_limit = int(request.POST.get("per_user_limit", 1) or 1)

        first_purchase_only = request.POST.get("first_purchase_only") == "on"
        existing_users_only = request.POST.get("existing_users_only") == "on"

        allowed_plans = request.POST.getlist("allowed_plans")
        allowed_emails = request.POST.get("allowed_emails", "").strip()

        if PromoCode.objects.filter(code__iexact=code).exclude(id=promo.id).exists():
            messages.error(request, f"Another promo code with the code '{code}' already exists.")
            return render(request, "payments/admin_promo_form.html", {"title": f"Edit {promo.code}", "action": "edit", "promo": promo})

        old_data = {"code": promo.code, "is_active": promo.is_active, "discount_value": str(promo.discount_value)}

        promo.code = code
        promo.description = description
        promo.admin_notes = admin_notes
        promo.discount_type = discount_type
        promo.discount_value = decimal.Decimal(discount_value_str or "0.00")
        promo.max_discount_amount = decimal.Decimal(max_discount_str) if max_discount_str else None
        promo.extra_validity_days = extra_days
        promo.extra_validity_months = extra_months
        promo.extra_validity_years = extra_years
        promo.is_active = is_active
        promo.is_public = is_public
        promo.auto_apply = auto_apply
        promo.stackable = stackable
        promo.priority = priority

        promo.start_date = timezone.datetime.fromisoformat(start_date_str) if start_date_str else None
        promo.end_date = timezone.datetime.fromisoformat(end_date_str) if end_date_str else None

        promo.min_purchase_amount = decimal.Decimal(min_purchase_str or "0.00")
        promo.max_purchase_amount = decimal.Decimal(max_purchase_str) if max_purchase_str else None
        promo.overall_usage_limit = int(overall_limit_str) if overall_limit_str else None
        promo.per_user_limit = per_user_limit
        promo.first_purchase_only = first_purchase_only
        promo.existing_users_only = existing_users_only
        promo.allowed_plans = allowed_plans
        promo.allowed_emails = allowed_emails
        promo.save()

        log_promo_action(promo, "UPDATED", request.user, {"before": old_data, "after": {"code": promo.code, "is_active": promo.is_active}})
        messages.success(request, f"Promo Code '{promo.code}' updated successfully!")
        return redirect("admin_promo_dashboard")

    context = {
        "title": f"Edit Promo Code: {promo.code}",
        "action": "edit",
        "promo": promo,
        "all_plans": ["Monthly", "Yearly", "Lifetime"]
    }
    return render(request, "payments/admin_promo_form.html", context)


@user_passes_test(is_authorized_admin)
@require_POST
def admin_promo_duplicate(request, promo_id):
    """
    Duplicates/Clones an existing Promo Code into a new draft promo.
    """
    original = get_object_or_404(PromoCode, id=promo_id)
    new_code = f"{original.code}_COPY"
    suffix = 1
    while PromoCode.objects.filter(code=new_code).exists():
        new_code = f"{original.code}_COPY{suffix}"
        suffix += 1

    clone = PromoCode.objects.create(
        code=new_code,
        description=f"Cloned from {original.code}. {original.description}",
        admin_notes=original.admin_notes,
        discount_type=original.discount_type,
        discount_value=original.discount_value,
        max_discount_amount=original.max_discount_amount,
        extra_validity_days=original.extra_validity_days,
        extra_validity_months=original.extra_validity_months,
        extra_validity_years=original.extra_validity_years,
        is_active=False,  # default inactive so admin can review
        is_public=original.is_public,
        auto_apply=False,
        stackable=original.stackable,
        priority=original.priority,
        start_date=original.start_date,
        end_date=original.end_date,
        min_purchase_amount=original.min_purchase_amount,
        max_purchase_amount=original.max_purchase_amount,
        overall_usage_limit=original.overall_usage_limit,
        per_user_limit=original.per_user_limit,
        first_purchase_only=original.first_purchase_only,
        existing_users_only=original.existing_users_only,
        allowed_plans=original.allowed_plans,
        allowed_emails=original.allowed_emails,
        created_by=request.user
    )

    log_promo_action(clone, "DUPLICATED", request.user, {"cloned_from": original.code, "new_code": clone.code})
    messages.success(request, f"Cloned promo '{original.code}' to new promo '{clone.code}' (Inactive).")
    return redirect("admin_promo_edit", promo_id=clone.id)


@user_passes_test(is_authorized_admin)
@require_POST
def admin_promo_toggle_status(request, promo_id):
    """
    Toggles is_active state of a promo code.
    """
    promo = get_object_or_404(PromoCode, id=promo_id)
    promo.is_active = not promo.is_active
    promo.save(update_fields=["is_active", "updated_at"])

    action_str = "ACTIVATED" if promo.is_active else "DEACTIVATED"
    log_promo_action(promo, action_str, request.user, {"is_active": promo.is_active})
    messages.success(request, f"Promo Code '{promo.code}' is now {action_str.lower()}.")
    return redirect("admin_promo_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_promo_archive(request, promo_id):
    """
    Archives a promo code.
    """
    promo = get_object_or_404(PromoCode, id=promo_id)
    promo.is_archived = True
    promo.is_active = False
    promo.save(update_fields=["is_archived", "is_active", "updated_at"])

    log_promo_action(promo, "ARCHIVED", request.user, {"is_archived": True})
    messages.info(request, f"Promo Code '{promo.code}' has been archived.")
    return redirect("admin_promo_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_promo_delete(request, promo_id):
    """
    Deletes a promo code if 0 redemptions, or archives if redemptions exist to preserve history.
    """
    promo = get_object_or_404(PromoCode, id=promo_id)
    if promo.redemptions.exists():
        promo.is_archived = True
        promo.is_active = False
        promo.save(update_fields=["is_archived", "is_active", "updated_at"])
        log_promo_action(promo, "ARCHIVED", request.user, {"reason": "Deleted with redemptions -> Archived"})
        messages.warning(request, f"Promo Code '{promo.code}' has active redemptions and was archived instead of deleted to protect historical invoices.")
    else:
        log_promo_action(promo, "DELETED", request.user, {"deleted_code": promo.code})
        promo.delete()
        messages.success(request, f"Promo Code '{promo.code}' deleted permanently.")

    return redirect("admin_promo_dashboard")


@user_passes_test(is_authorized_admin)
@require_POST
def admin_promo_bulk_action(request):
    """
    Handles bulk activate, bulk deactivate, bulk archive actions.
    """
    action = request.POST.get("bulk_action")
    promo_ids = request.POST.getlist("selected_promos")

    if not promo_ids:
        messages.error(request, "No promo codes selected for bulk action.")
        return redirect("admin_promo_dashboard")

    promos = PromoCode.objects.filter(id__in=promo_ids)
    count = promos.count()

    if action == "activate":
        promos.update(is_active=True, is_archived=False, updated_at=timezone.now())
        messages.success(request, f"Activated {count} promo codes.")
    elif action == "deactivate":
        promos.update(is_active=False, updated_at=timezone.now())
        messages.warning(request, f"Deactivated {count} promo codes.")
    elif action == "archive":
        promos.update(is_archived=True, is_active=False, updated_at=timezone.now())
        messages.info(request, f"Archived {count} promo codes.")
    else:
        messages.error(request, "Invalid bulk action requested.")

    return redirect("admin_promo_dashboard")


@user_passes_test(is_authorized_admin)
def admin_promo_export_csv(request):
    """
    Exports all non-archived promo codes and usage metrics to CSV.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="promo_codes_export_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Code", "Discount Type", "Discount Value", "Max Discount Cap", "Extra Days",
        "Status", "Is Public", "Auto Apply", "Priority", "Start Date", "End Date",
        "Usage Count", "Global Limit", "Per User Limit", "Min Purchase Amount", "Allowed Plans"
    ])

    promos = PromoCode.objects.all().order_by("-created_at")
    for p in promos:
        writer.writerow([
            p.code,
            p.get_discount_type_display(),
            str(p.discount_value),
            str(p.max_discount_amount) if p.max_discount_amount else "None",
            p.total_extra_days,
            p.status_label,
            "Yes" if p.is_public else "No",
            "Yes" if p.auto_apply else "No",
            p.priority,
            p.start_date.strftime("%Y-%m-%d %H:%M") if p.start_date else "None",
            p.end_date.strftime("%Y-%m-%d %H:%M") if p.end_date else "None",
            p.overall_usage_count,
            p.overall_usage_limit or "Unlimited",
            p.per_user_limit,
            str(p.min_purchase_amount),
            ", ".join(p.allowed_plans) if p.allowed_plans else "All Plans"
        ])

    return response


@user_passes_test(is_authorized_admin)
def admin_promo_audit_logs(request):
    """
    Renders audit logs and full redemption logs for superuser oversight.
    """
    search_query = request.GET.get("search", "")

    logs = PromoAuditLog.objects.select_related("performed_by", "promo_code").order_by("-timestamp")
    redemptions = PromoRedemption.objects.select_related("promo_code", "user", "subscription").order_by("-redeemed_at")

    if search_query:
        logs = logs.filter(
            models.Q(code_str__icontains=search_query) |
            models.Q(action__icontains=search_query) |
            models.Q(performed_by__email__icontains=search_query)
        )
        redemptions = redemptions.filter(
            models.Q(promo_code__code__icontains=search_query) |
            models.Q(user__email__icontains=search_query)
        )

    context = {
        "title": "Promo Audit & Redemption Logs",
        "audit_logs": logs[:100],
        "redemptions": redemptions[:100],
        "search_query": search_query
    }
    return render(request, "payments/admin_promo_logs.html", context)
