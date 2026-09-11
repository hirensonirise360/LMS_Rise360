from django.contrib import admin
from django.db.models import Count, Q
from .models import EAPart, EADomain, EATopic, EATopicEbook, EATopicVideo


class EADomainInline(admin.TabularInline):
    model = EADomain
    extra = 0
    fields = ("name", "order")
    show_change_link = True


class EATopicInline(admin.TabularInline):
    model = EATopic
    extra = 0
    fields = ("name", "order")
    show_change_link = True


@admin.register(EAPart)
class EAPartAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "is_active", "description", "domain_count_display", "topic_count_display")
    list_editable = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("number", "name", "description")
    ordering = ("number",)
    save_on_top = True
    actions = ["make_active", "make_inactive"]
    inlines = [EADomainInline]
    fieldsets = (
        (None, {
            "fields": ("number", "name", "is_active", "description")
        }),
    )

    @admin.action(description="Mark selected modules as Active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} module(s) marked as Active.")

    @admin.action(description="Mark selected modules as Inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} module(s) marked as Inactive.")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _domain_count=Count("domains", distinct=True),
            _topic_count=Count("domains__topics", distinct=True)
        )

    def domain_count_display(self, obj):
        return getattr(obj, "_domain_count", 0)
    domain_count_display.short_description = "Domains"
    domain_count_display.admin_order_field = "_domain_count"

    def topic_count_display(self, obj):
        return getattr(obj, "_topic_count", 0)
    topic_count_display.short_description = "Topics"
    topic_count_display.admin_order_field = "_topic_count"


@admin.register(EADomain)
class EADomainAdmin(admin.ModelAdmin):
    list_display = ("name", "part", "order", "topic_count_display")
    list_filter = ("part",)
    search_fields = ("name", "part__name")
    list_editable = ("order",)
    list_select_related = ("part",)
    ordering = ("part__number", "order")
    save_on_top = True
    inlines = [EATopicInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_topic_count=Count("topics", distinct=True))

    def topic_count_display(self, obj):
        return getattr(obj, "_topic_count", 0)
    topic_count_display.short_description = "Topics"
    topic_count_display.admin_order_field = "_topic_count"


# ── Filters ──────────────────────────────────────────────────────────────────

class HasEbookFilter(admin.SimpleListFilter):
    title = "E-Book"
    parameter_name = "has_ebook"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Has E-Book"),
            ("no",  "Missing E-Book"),
        )

    def queryset(self, request, queryset):
        has = Q(pdf_file__isnull=False) & ~Q(pdf_file="")
        supabase = ~Q(supabase_pdf_path="")
        if self.value() == "yes":
            return queryset.filter(has | supabase)
        if self.value() == "no":
            return queryset.exclude(has | supabase)
        return queryset


class HasVideoFilter(admin.SimpleListFilter):
    title = "Video"
    parameter_name = "has_video"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Has Video"),
            ("no",  "Missing Video"),
        )

    def queryset(self, request, queryset):
        has_file = Q(video_file__isnull=False) & ~Q(video_file="")
        has_url  = ~Q(video_external_url="")
        if self.value() == "yes":
            return queryset.filter(has_file | has_url)
        if self.value() == "no":
            return queryset.exclude(has_file | has_url)
        return queryset


# ── EATopic Admin ─────────────────────────────────────────────────────────────

@admin.register(EATopic)
class EATopicAdmin(admin.ModelAdmin):
    list_display = (
        "name", "domain", "order",
        "has_ebook", "has_video",
        "ebook_source", "video_source",
    )
    list_filter = ("domain__part", "domain", HasEbookFilter, HasVideoFilter)
    search_fields = ("name", "domain__name", "domain__part__name")
    list_editable = ("order",)
    list_select_related = ("domain", "domain__part")
    ordering = ("domain__part__number", "domain__order", "order")
    save_on_top = True
    fieldsets = (
        ("Topic Information", {
            "fields": ("domain", "name", "order")
        }),
        ("E-Book Content", {
            "description": "Upload a PDF file OR paste the Supabase storage path for private E-Books.",
            "fields": ("pdf_file", "supabase_pdf_path"),
        }),
        ("Video Content", {
            "description": "Upload a video file OR paste a YouTube / Vimeo URL.",
            "fields": ("video_file", "video_external_url"),
        }),
    )

    def has_ebook(self, obj):
        return bool(obj.pdf_file or obj.supabase_pdf_path)
    has_ebook.boolean = True
    has_ebook.short_description = "E-Book ✓"

    def has_video(self, obj):
        return bool(obj.video_file or obj.video_external_url)
    has_video.boolean = True
    has_video.short_description = "Video ✓"

    def ebook_source(self, obj):
        if obj.supabase_pdf_path:
            return "☁ Supabase"
        if obj.pdf_file:
            return "📁 File"
        return "—"
    ebook_source.short_description = "E-Book Source"

    def video_source(self, obj):
        if obj.video_external_url:
            return "🔗 URL"
        if obj.video_file:
            return "📁 File"
        return "—"
    video_source.short_description = "Video Source"


# ── E-Book Admin (proxy) ─────────────────────────────────────────────────────

@admin.register(EATopicEbook)
class EATopicEbookAdmin(admin.ModelAdmin):
    """
    Dedicated E-Book management view.
    Shows every Topic with its e-book status.
    Supabase path is editable inline; PDF file upload is in the change form.
    """
    list_display = (
        "topic_name",
        "module",
        "domain_name",
        "ebook_status",
        "supabase_pdf_path",
    )
    list_editable = ("supabase_pdf_path",)
    list_filter = (HasEbookFilter, "domain__part", "domain")
    search_fields = ("name", "domain__name", "domain__part__name", "supabase_pdf_path")
    list_select_related = ("domain", "domain__part")
    ordering = ("domain__part__number", "domain__order", "order")
    save_on_top = True

    # Show only E-Book relevant fields in the change form
    fieldsets = (
        ("Topic", {
            "fields": ("domain", "name"),
        }),
        ("E-Book Content", {
            "description": (
                "Choose one: either paste the Supabase storage path (private bucket) "
                "OR upload a PDF file directly."
            ),
            "fields": ("supabase_pdf_path", "pdf_file"),
        }),
    )

    def topic_name(self, obj):
        return obj.name
    topic_name.short_description = "Topic"
    topic_name.admin_order_field = "name"

    def module(self, obj):
        return obj.domain.part.name
    module.short_description = "Module"
    module.admin_order_field = "domain__part__name"

    def domain_name(self, obj):
        return obj.domain.name
    domain_name.short_description = "Domain"
    domain_name.admin_order_field = "domain__name"

    def ebook_status(self, obj):
        if obj.supabase_pdf_path:
            return "☁ Supabase"
        if obj.pdf_file:
            return "📁 File"
        return "❌ Missing"
    ebook_status.short_description = "E-Book"


# ── Video Admin (proxy) ──────────────────────────────────────────────────────

@admin.register(EATopicVideo)
class EATopicVideoAdmin(admin.ModelAdmin):
    """
    Dedicated Video management view.
    Shows every Topic with its video status.
    External URL is editable inline; video file upload is in the change form.
    """
    list_display = (
        "topic_name",
        "module",
        "domain_name",
        "video_status",
        "video_external_url",
    )
    list_editable = ("video_external_url",)
    list_filter = (HasVideoFilter, "domain__part", "domain")
    search_fields = ("name", "domain__name", "domain__part__name", "video_external_url")
    list_select_related = ("domain", "domain__part")
    ordering = ("domain__part__number", "domain__order", "order")
    save_on_top = True

    # Show only Video relevant fields in the change form
    fieldsets = (
        ("Topic", {
            "fields": ("domain", "name"),
        }),
        ("Video Content", {
            "description": (
                "Choose one: either paste a YouTube/Vimeo URL "
                "OR upload a video file directly."
            ),
            "fields": ("video_external_url", "video_file"),
        }),
    )

    def topic_name(self, obj):
        return obj.name
    topic_name.short_description = "Topic"
    topic_name.admin_order_field = "name"

    def module(self, obj):
        return obj.domain.part.name
    module.short_description = "Module"
    module.admin_order_field = "domain__part__name"

    def domain_name(self, obj):
        return obj.domain.name
    domain_name.short_description = "Domain"
    domain_name.admin_order_field = "domain__name"

    def video_status(self, obj):
        if obj.video_external_url:
            return "🔗 URL"
        if obj.video_file:
            return "📁 File"
        return "❌ Missing"
    video_status.short_description = "Video"
