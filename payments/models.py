import decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("fixed", "Fixed Amount (₹)"),
        ("percentage", "Percentage (%)"),
        ("free", "100% Free / Full Discount"),
        ("validity_only", "Extra Validity Only"),
    )

    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    discount_type = models.CharField(
        max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="fixed"
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=decimal.Decimal("0.00")
    )
    max_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum discount cap for percentage promos (e.g. 50% up to ₹500)",
    )

    # Extra validity
    extra_validity_days = models.PositiveIntegerField(default=0)
    extra_validity_months = models.PositiveIntegerField(default=0)
    extra_validity_years = models.PositiveIntegerField(default=0)

    # Rules & Restrictions
    is_active = models.BooleanField(default=True, db_index=True)
    is_public = models.BooleanField(
        default=True,
        db_index=True,
        help_text="If True, code is displayed publicly on checkout page",
    )
    auto_apply = models.BooleanField(
        default=False,
        db_index=True,
        help_text="If True, auto-applies on checkout if user qualifies",
    )
    stackable = models.BooleanField(
        default=False, help_text="Can be stacked with other promotions"
    )
    priority = models.IntegerField(
        default=0,
        db_index=True,
        help_text="Higher priority codes are evaluated first for auto-apply",
    )

    start_date = models.DateTimeField(null=True, blank=True, db_index=True)
    end_date = models.DateTimeField(null=True, blank=True, db_index=True)

    min_purchase_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=decimal.Decimal("0.00")
    )
    max_purchase_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    overall_usage_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text="Global maximum redemptions count"
    )
    overall_usage_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(
        default=1, help_text="Max redemptions per user"
    )

    first_purchase_only = models.BooleanField(
        default=False, help_text="Only for users with 0 previous paid subscriptions"
    )
    existing_users_only = models.BooleanField(
        default=False, help_text="Only for users with >=1 paid subscriptions"
    )

    allowed_plans = models.JSONField(
        default=list,
        blank=True,
        help_text="List of eligible plans e.g. ['Monthly', 'Yearly', 'Lifetime']",
    )
    allowed_emails = models.TextField(
        blank=True,
        help_text="Comma or newline separated list of allowed emails or domain suffixes (e.g. user@domain.com, @institute.com)",
    )
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="allowed_promos"
    )

    is_archived = models.BooleanField(default=False, db_index=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_promos",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-priority", "-created_at")

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    @property
    def total_extra_days(self):
        return (
            self.extra_validity_days
            + (self.extra_validity_months * 30)
            + (self.extra_validity_years * 365)
        )

    @property
    def status_label(self):
        if self.is_archived:
            return "Archived"
        if not self.is_active:
            return "Inactive"
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return "Upcoming"
        if self.end_date and now > self.end_date:
            return "Expired"
        if (
            self.overall_usage_limit
            and self.overall_usage_count >= self.overall_usage_limit
        ):
            return "Limit Reached"
        return "Active"

    def calculate_discount(self, original_amount):
        """Calculates discount amount capped by max_discount_amount if applicable."""
        orig = decimal.Decimal(str(original_amount))
        if orig <= 0:
            return decimal.Decimal("0.00")

        if self.discount_type == "free":
            return orig
        elif self.discount_type == "validity_only":
            return decimal.Decimal("0.00")
        elif self.discount_type == "fixed":
            disc = min(orig, self.discount_value)
            return disc.quantize(decimal.Decimal("0.01"))
        elif self.discount_type == "percentage":
            disc = (orig * self.discount_value) / decimal.Decimal("100.00")
            if self.max_discount_amount and self.max_discount_amount > 0:
                disc = min(disc, self.max_discount_amount)
            disc = min(orig, disc)
            return disc.quantize(decimal.Decimal("0.01"))
        return decimal.Decimal("0.00")


class Subscription(models.Model):
    PLAN_CHOICES = (
        ("Monthly", "Monthly"),
        ("Yearly", "Yearly"),
        ("Lifetime", "Lifetime"),
    )

    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Expired", "Expired"),
        ("Pending", "Pending"),
        ("Cancelled", "Cancelled"),
    )

    PAYMENT_STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="Lifetime", db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2) # Final amount payable
    original_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=decimal.Decimal("0.00")
    )
    applied_promo = models.ForeignKey(
        PromoCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions",
    )
    extra_days_granted = models.IntegerField(default=0)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True, db_index=True)
    lifetime = models.BooleanField(default=False, db_index=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending", db_index=True
    )
    remaining_days = models.IntegerField(null=True, blank=True)

    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending", db_index=True
    )
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.email} - {self.plan} ({self.status})"

    def calculate_remaining_days(self):
        if self.payment_status != "Paid" or self.status == "Cancelled":
            return 0
        if self.lifetime:
            return None
        if not self.end_date:
            return 0

        today = timezone.now().date()
        end_date = (
            self.end_date.date() if hasattr(self.end_date, "date") else self.end_date
        )
        delta = end_date - today
        return max(0, delta.days)

    def update_status(self):
        """Dynamically updates status and remaining days."""
        changed = False
        if self.payment_status == "Paid" and self.status != "Cancelled":
            if self.lifetime:
                if self.status != "Active":
                    self.status = "Active"
                    changed = True
                if self.remaining_days is not None:
                    self.remaining_days = None
                    changed = True
            else:
                rem = self.calculate_remaining_days()
                if self.remaining_days != rem:
                    self.remaining_days = rem
                    changed = True

                if rem <= 0:
                    if self.status != "Expired":
                        self.status = "Expired"
                        changed = True
                else:
                    if self.status != "Active":
                        self.status = "Active"
                        changed = True
        else:
            if self.status not in ["Pending", "Cancelled"]:
                self.status = "Pending"
                changed = True

        if changed:
            self.save(update_fields=["status", "remaining_days", "updated_at"])


class Payment(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Success", "Success"),
        ("Failed", "Failed"),
    )

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=decimal.Decimal("0.00")
    )
    promo_code = models.ForeignKey(
        PromoCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
    )

    gateway = models.CharField(max_length=50, db_index=True)  # Razorpay, QR Code, Free
    transaction_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    order_id = models.CharField(max_length=100, null=True, blank=True)
    signature = models.CharField(max_length=255, null=True, blank=True)

    # QR verification fields
    utr_number = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    screenshot = models.ImageField(
        upload_to="payment_screenshots/%Y/%m/%d/", null=True, blank=True
    )

    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Pending", db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.gateway} - {self.status}"


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="invoices"
    )
    original_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=decimal.Decimal("0.00")
    )
    promo_code_str = models.CharField(max_length=50, null=True, blank=True)

    amount = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Base amount before tax (or net subtotal)
    gst = models.DecimalField(max_digits=10, decimal_places=2)  # GST portion
    total = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Final total paid
    payment_status = models.CharField(max_length=50, db_index=True)  # Paid, Pending, Failed
    pdf_path = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.email} - Total: ₹{self.total}"


class PromoRedemption(models.Model):
    STATUS_CHOICES = (
        ("applied", "Applied/Pending"),
        ("redeemed", "Redeemed/Completed"),
        ("cancelled", "Cancelled/Refunded"),
    )

    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.CASCADE, related_name="redemptions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="promo_redemptions",
    )
    subscription = models.ForeignKey(
        Subscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="promo_redemptions",
    )
    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="promo_redemptions",
    )
    invoice = models.ForeignKey(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="promo_redemptions",
    )

    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    extra_days_granted = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="redeemed"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    redeemed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-redeemed_at",)

    def __str__(self):
        return f"{self.user.email} redeemed {self.promo_code.code} on {self.redeemed_at.strftime('%Y-%m-%d')}"


class PromoAuditLog(models.Model):
    promo_code = models.ForeignKey(
        PromoCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    code_str = models.CharField(max_length=50)
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return f"{self.action} on {self.code_str} by {self.performed_by} at {self.timestamp}"
