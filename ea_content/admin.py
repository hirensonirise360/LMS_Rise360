from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EANote, Flashcard, FlashcardSRS
)
from ea_exam.models import EATopicResource





@admin.register(EANote)
class EANoteAdmin(admin.ModelAdmin):
    list_display = ("title", "part", "domain", "topic", "is_admin_note", "author", "created_at")
    list_filter = ("part", "domain", "topic", "is_admin_note")
    search_fields = ("title", "content")
    raw_id_fields = ("author",)
    fieldsets = (
        (None, {"fields": ("title", "part", "domain", "topic", "content", "is_admin_note", "author")}),
    )


@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ("short_front", "part", "domain", "topic", "difficulty", "is_published")
    list_filter = ("part", "domain", "difficulty", "is_published")
    search_fields = ("front", "back")
    list_editable = ("difficulty", "is_published")

    def short_front(self, obj):
        return obj.front[:80]
    short_front.short_description = "Front"


@admin.register(EATopicResource)
class EATopicResourceAdmin(admin.ModelAdmin):
    list_display  = ("title", "topic_name", "resource_type", "original_filename", "file_size_display", "uploaded_at")
    list_filter   = ("resource_type", "topic__domain__part", "topic__domain")
    search_fields = ("title", "original_filename", "supabase_path", "topic__name")
    readonly_fields = ("supabase_path", "original_filename", "file_size_bytes", "uploaded_at", "updated_at")

    def topic_name(self, obj):
        return str(obj.topic)
    topic_name.short_description = "Topic"

    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = "Size"
