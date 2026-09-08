from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EANote, Flashcard, FlashcardSRS
)




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

