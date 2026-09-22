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
    question_file = models.FileField(upload_to="ea_questions/", null=True, blank=True, help_text=_("Question file in any format (Excel, Word, Text, PDF, etc.)"))
    supabase_question_path = models.CharField(max_length=500, blank=True, default="", help_text=_("Path in Supabase storage if stored remotely"))

    class Meta:
        ordering = ["domain", "order"]
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")

    def __str__(self):
        return f"{self.domain.part.number}.{self.domain.name} › {self.name}"

    @property
    def all_ebook_files(self):
        """Returns all study material files attached to this topic, including primary pdf_file."""
        from django.urls import reverse
        def get_icon(filename):
            fn = (filename or "").lower()
            if fn.endswith('.pdf'): return 'fas fa-file-pdf text-danger'
            if fn.endswith(('.ppt', '.pptx')): return 'fas fa-file-powerpoint text-warning'
            if fn.endswith(('.xls', '.xlsx', '.csv')): return 'fas fa-file-excel text-success'
            if fn.endswith(('.doc', '.docx')): return 'fas fa-file-word text-primary'
            if fn.endswith(('.txt', '.text', '.md')): return 'fas fa-file-alt text-secondary'
            return 'fas fa-file text-secondary'

        items = []
        if self.pdf_file or self.supabase_pdf_path:
            name = self.pdf_file.name.split("/")[-1] if self.pdf_file else self.supabase_pdf_path.split("/")[-1]
            try:
                main_url = self.pdf_file.url if self.pdf_file else reverse("serve_ebook_pdf", kwargs={"topic_id": self.pk})
            except Exception:
                main_url = self.pdf_file.url if self.pdf_file else None
            items.append({
                "id": f"main_{self.pk}",
                "file_id": None,
                "is_main": True,
                "title": name,
                "icon": get_icon(name),
                "pdf_file": self.pdf_file,
                "supabase_pdf_path": self.supabase_pdf_path,
                "url": main_url,
            })
        for f in self.ebook_files.all():
            try:
                f_url = f.pdf_file.url if f.pdf_file else reverse("serve_ebook_file_pdf", kwargs={"file_id": f.pk})
            except Exception:
                f_url = f.pdf_file.url if f.pdf_file else None
            items.append({
                "id": f"file_{f.pk}",
                "file_id": f.pk,
                "is_main": False,
                "title": f.display_name,
                "icon": get_icon(f.display_name),
                "pdf_file": f.pdf_file,
                "supabase_pdf_path": f.supabase_pdf_path,
                "url": f_url,
            })
        return items

    @property
    def has_ebook(self):
        """Returns True if any study material, ebook, or resource is attached to this topic."""
        return bool(
            self.pdf_file
            or self.supabase_pdf_path
            or self.ebook_files.exists()
            or (hasattr(self, 'resources') and self.resources.exists())
        )

    @property
    def ebook_count(self):
        cnt = self.ebook_files.count()
        if self.pdf_file or self.supabase_pdf_path:
            cnt += 1
        return cnt


class EATopicEbookFile(models.Model):
    """Stores multiple E-Book/PDF files per topic."""
    topic = models.ForeignKey(EATopic, on_delete=models.CASCADE, related_name="ebook_files")
    pdf_file = models.FileField(upload_to="ea_ebooks/", null=True, blank=True)
    supabase_pdf_path = models.CharField(max_length=500, blank=True, default="", help_text=_("Path in Supabase 'ea-ebooks' private bucket"))
    title = models.CharField(max_length=255, blank=True, help_text=_("Display title / original filename"))
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = _("Topic E-Book File")
        verbose_name_plural = _("Topic E-Book Files")

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        if self.title:
            return self.title
        if self.pdf_file:
            return self.pdf_file.name.split("/")[-1]
        if self.supabase_pdf_path:
            return self.supabase_pdf_path.split("/")[-1]
        return _("E-Book PDF")


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


# ──────────────────────────────────────────────
# TOPIC RESOURCES (files stored in Supabase)
# ──────────────────────────────────────────────

class EATopicResource(models.Model):
    """
    Stores supplementary learning materials (Excel, PPT, PDF, Word, Text, etc.)
    for a given topic. Files are stored in the private 'topic-resources'
    Supabase bucket at path:
        topic_resources/{part_number}/{domain_slug}/{topic_id}/{filename}
    """

    RESOURCE_TYPE_CHOICES = [
        ("pdf",   _("PDF Document")),
        ("excel", _("Excel Spreadsheet")),
        ("ppt",   _("PowerPoint Presentation")),
        ("word",  _("Word Document")),
        ("text",  _("Text File")),
        ("other", _("Other")),
    ]

    # Extension → resource_type mapping used during upload
    EXTENSION_TYPE_MAP = {
        "pdf":  "pdf",
        "xls":  "excel", "xlsx": "excel", "csv": "excel",
        "ppt":  "ppt",   "pptx": "ppt",
        "doc":  "word",  "docx": "word",
        "txt":  "text",  "md":   "text",
    }

    topic             = models.ForeignKey(EATopic, on_delete=models.CASCADE, related_name="resources")
    title             = models.CharField(max_length=255)
    resource_type     = models.CharField(max_length=10, choices=RESOURCE_TYPE_CHOICES, default="other")
    supabase_path     = models.CharField(max_length=600, help_text=_("Path inside the 'topic-resources' bucket"))
    original_filename = models.CharField(max_length=255, blank=True)
    file_size_bytes   = models.PositiveBigIntegerField(default=0)
    uploaded_at       = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resource_type", "title"]
        verbose_name = _("Topic Resource")
        verbose_name_plural = _("Topic Resources")

    def __str__(self):
        return f"{self.title} ({self.topic})"

    @property
    def icon_class(self):
        icons = {
            "pdf":   "fas fa-file-pdf text-danger",
            "excel": "fas fa-file-excel text-success",
            "ppt":   "fas fa-file-powerpoint text-warning",
            "word":  "fas fa-file-word text-primary",
            "text":  "fas fa-file-alt text-secondary",
            "other": "fas fa-file text-muted",
        }
        return icons.get(self.resource_type, "fas fa-file text-muted")

    @property
    def file_size_display(self):
        """Human-readable file size."""
        size = self.file_size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / 1024 ** 2:.1f} MB"

    @classmethod
    def detect_type(cls, filename: str) -> str:
        """Detect resource_type from file extension."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return cls.EXTENSION_TYPE_MAP.get(ext, "other")
