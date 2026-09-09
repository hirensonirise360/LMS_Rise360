from django.contrib import admin
from django.utils.html import format_html
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, BooleanWidget
from import_export.admin import ImportExportModelAdmin
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import path
import csv
import io
from .models import (
    EAPart, EADomain, EATopic,
    EAQuestion, EAExamSession, QuestionUserNote
)


class EADomainInline(admin.TabularInline):
    model = EADomain
    extra = 0
    fields = ("name", "order")


class EATopicInline(admin.TabularInline):
    model = EATopic
    extra = 0
    fields = ("name", "order")


@admin.register(EAPart)
class EAPartAdmin(admin.ModelAdmin):
    list_display = ("number", "name")
    inlines = [EADomainInline]


@admin.register(EADomain)
class EADomainAdmin(admin.ModelAdmin):
    list_display = ("name", "part", "order")
    list_filter = ("part",)
    search_fields = ("name",)
    inlines = [EATopicInline]


@admin.register(EATopic)
class EATopicAdmin(admin.ModelAdmin):
    list_display = ("name", "domain", "order", "has_ebook", "has_video")
    list_filter = ("domain__part", "domain")
    search_fields = ("name",)
    fieldsets = (
        ("Topic Information", {
            "fields": ("domain", "name", "order")
        }),
        ("E-Book Content", {
            "fields": ("pdf_file", "supabase_pdf_path")
        }),
        ("Video Content", {
            "fields": ("video_file", "video_external_url")
        }),
    )

    def has_ebook(self, obj):
        return bool(obj.pdf_file or obj.supabase_pdf_path)
    has_ebook.boolean = True
    has_ebook.short_description = "Has E-Book"

    def has_video(self, obj):
        return bool(obj.video_file or obj.video_external_url)
    has_video.boolean = True
    has_video.short_description = "Has Video"


class EAQuestionResource(resources.ModelResource):
    part = fields.Field(column_name='part', attribute='part', widget=ForeignKeyWidget(EAPart, 'pk'))
    domain = fields.Field(column_name='domain', attribute='domain', widget=ForeignKeyWidget(EADomain, 'pk'))
    topic = fields.Field(column_name='topic', attribute='topic', widget=ForeignKeyWidget(EATopic, 'pk'))

    choice1_text = fields.Field(column_name='choice1_text', attribute='choice_1')
    choice1_correct = fields.Field(column_name='choice1_correct', attribute='choice_1_correct', widget=BooleanWidget())
    
    choice2_text = fields.Field(column_name='choice2_text', attribute='choice_2')
    choice2_correct = fields.Field(column_name='choice2_correct', attribute='choice_2_correct', widget=BooleanWidget())
    
    choice3_text = fields.Field(column_name='choice3_text', attribute='choice_3')
    choice3_correct = fields.Field(column_name='choice3_correct', attribute='choice_3_correct', widget=BooleanWidget())
    
    choice4_text = fields.Field(column_name='choice4_text', attribute='choice_4')
    choice4_correct = fields.Field(column_name='choice4_correct', attribute='choice_4_correct', widget=BooleanWidget())

    class Meta:
        model = EAQuestion
        import_id_fields = ('id',)
        fields = (
            "id", "part", "domain", "topic",
            "question_text", "explanation", "difficulty", "status",
            "choice1_text", "choice1_correct",
            "choice2_text", "choice2_correct",
            "choice3_text", "choice3_correct",
            "choice4_text", "choice4_correct"
        )
        export_order = fields


@admin.register(EAQuestion)
class EAQuestionAdmin(ImportExportModelAdmin):
    resource_class = EAQuestionResource
    list_display = (
        "id", "short_text", "part", "domain", "topic",
        "difficulty_badge", "status", "delete_row"
    )
    list_filter = ("part", "domain", "topic", "difficulty", "status")
    search_fields = ("question_text",)
    list_per_page = 25
    readonly_fields = ("created_at", "updated_at")
    ordering = ("id",)
    import_template_name = "admin/ea_exam/eaquestion/import.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download-csv-template/', self.admin_site.admin_view(self.download_csv_template), name='ea_question_template'),
        ]
        return custom_urls + urls

    def download_csv_template(self, request):
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = [
            "id", "part", "domain", "topic", "question_text", "explanation", "difficulty", "status", 
            "choice1_text", "choice1_correct",
            "choice2_text", "choice2_correct",
            "choice3_text", "choice3_correct",
            "choice4_text", "choice4_correct"
        ]
        writer.writerow(headers)
        
        writer.writerow([
            "100001", "1", "1", "", "What is the standard deduction for a single filer for 2024?", 
            "Standard deduction for single 2024 is $14,600.", "medium", "active",
            "$12,950", "0",
            "$13,850", "0",
            "$14,600", "1",
            "$29,200", "0"
        ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="mcq_import_template.csv"'
        return response

    def delete_row(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:ea_exam_eaquestion_delete', args=[obj.pk])
        return format_html('<a class="deletelink" href="{}">Delete</a>', url)
    delete_row.short_description = "Action"

    fieldsets = (
        ("Question Info", {"fields": ("part", "domain", "topic", "question_text", "explanation")}),
        ("MCQ Choices", {
            "fields": (
                ("choice_1", "choice_1_correct"),
                ("choice_2", "choice_2_correct"),
                ("choice_3", "choice_3_correct"),
                ("choice_4", "choice_4_correct"),
            )
        }),
        ("Metadata", {"fields": ("difficulty", "status")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def short_text(self, obj):
        return obj.question_text[:80] + "..." if len(obj.question_text) > 80 else obj.question_text

    def difficulty_badge(self, obj):
        colors = {"easy": "green", "medium": "orange", "hard": "red"}
        color = colors.get(obj.difficulty, "gray")
        return format_html(
            '<span style="color:white;background:{};padding:2px 8px;border-radius:4px;">{}</span>',
            color, obj.get_difficulty_display()
        )
    difficulty_badge.short_description = "Difficulty"
    short_text.short_description = "Question"


@admin.register(QuestionUserNote)
class QuestionUserNoteAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "content_short", "updated_at")
    list_filter = ("user", "updated_at")
    search_fields = ("content", "user__email", "question__question_text")

    def content_short(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
