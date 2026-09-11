import json
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


# ──────────────────────────────────────────────
# EA DOMAIN TAXONOMY
# ──────────────────────────────────────────────

class EAPart(models.Model):
    number = models.PositiveSmallIntegerField(unique=True, help_text=_("Display order / module number"))
    name = models.CharField(max_length=200, help_text=_("Topic name, e.g. MS Excel, Bookkeeping, Canadian Taxation"))
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text=_("Designates whether this module is active and accessible to students."))

    class Meta:
        ordering = ["number"]
        verbose_name = _("Learning Topic / Module")
        verbose_name_plural = _("Learning Topics / Modules")

    def __str__(self):
        return f"{self.name}"


class EADomain(models.Model):
    part = models.ForeignKey(EAPart, on_delete=models.CASCADE, related_name="domains")
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["part", "order"]
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")

    def __str__(self):
        return f"{self.part} › {self.name}"


class EATopic(models.Model):
    domain = models.ForeignKey(EADomain, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    # Content fields consolidated into Topic
    video_file = models.FileField(upload_to="ea_videos/", null=True, blank=True)
    video_external_url = models.URLField(blank=True, help_text=_("YouTube/Vimeo link"))
    pdf_file = models.FileField(upload_to="ea_ebooks/", null=True, blank=True)
    supabase_pdf_path = models.CharField(max_length=500, blank=True, default="", help_text=_("Path in Supabase 'ea-ebooks' private bucket"))

    class Meta:
        ordering = ["domain", "order"]
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")

    def __str__(self):
        return f"{self.domain.part.number}.{self.domain.name} › {self.name}"


class EATopicEbook(EATopic):
    """Proxy model for managing E-Book content per Topic (no new DB table)."""
    class Meta:
        proxy = True
        verbose_name = _("E-Book")
        verbose_name_plural = _("E-Books")


class EATopicVideo(EATopic):
    """Proxy model for managing Video content per Topic (no new DB table)."""
    class Meta:
        proxy = True
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")


# ──────────────────────────────────────────────
# USER PROGRESS / PART GATING
# ──────────────────────────────────────────────

class UserProgress(models.Model):
    """
    Tracks which EA Part the student is currently active on.
    active_part: the highest unlocked part (1, 2, or 3).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ea_user_progress"
    )
    active_part = models.PositiveSmallIntegerField(default=1)
    last_accessed_topic = models.ForeignKey(
        "EATopic", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("User Progress")

    def __str__(self):
        return f"{self.user} — Active Part: {self.active_part}"

    def is_part_complete(self, part_number):
        """
        Returns True if average domain accuracy for the given part >= 80%.
        Uses DomainAccuracy records from ea_analytics.
        Falls back to False if no data exists.
        """
        from ea_analytics.models import DomainAccuracy
        domain_accs = DomainAccuracy.objects.filter(
            user=self.user, part_number=part_number
        )
        if not domain_accs.exists():
            return False
        total_accuracy = sum(da.accuracy_pct for da in domain_accs)
        avg_accuracy = total_accuracy / domain_accs.count()
        return avg_accuracy >= 80


class UserTopicReadStatus(models.Model):
    """
    Tracks if a user has marked a specific topic as 'Read' or 'Completed'.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_read_statuses"
    )
    topic = models.ForeignKey(EATopic, on_delete=models.CASCADE, related_name="read_statuses")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "topic")
        verbose_name = _("User Topic Read Status")
        verbose_name_plural = _("User Topic Read Statuses")
        indexes = [
            models.Index(fields=["user", "topic"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.topic.name} - Read: {self.is_read}"
