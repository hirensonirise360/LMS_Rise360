from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Program, Course, Upload


class ProgramAdmin(TranslationAdmin):
    pass


class CourseAdmin(TranslationAdmin):
    pass


class UploadAdmin(TranslationAdmin):
    pass


admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Upload, UploadAdmin)
