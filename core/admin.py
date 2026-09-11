from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import NewsAndEvents, BlogArticle


class NewsAndEventsAdmin(TranslationAdmin):
    pass


@admin.register(BlogArticle)
class BlogArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "created_at", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    fieldsets = (
        ("Content", {"fields": ("title", "slug", "content", "meta_description")}),
        ("Publishing", {"fields": ("is_published",)}),
    )


admin.site.register(NewsAndEvents, NewsAndEventsAdmin)
