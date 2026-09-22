from django.urls import path
from . import views

urlpatterns = [
    # eBooks
    path("", views.ebook_library, name="ebook_library"),
    path("ebooks/view/<int:topic_id>/", views.serve_ebook_pdf, name="serve_ebook_pdf"),
    path("ebooks/file/<int:file_id>/view/", views.serve_ebook_file_pdf, name="serve_ebook_file_pdf"),
    path("ebooks/<int:topic_id>/json/", views.topic_ebooks_json, name="topic_ebooks_json"),
    
    # Admin eBook Configurator
    path("admin/ebooks/", views.admin_ebook_manager, name="admin_ebook_manager"),
    path("admin/ebooks/<int:topic_id>/upload/", views.admin_upload_pdf, name="admin_upload_pdf"),
    path("admin/ebooks/<int:topic_id>/delete/", views.admin_delete_pdf, name="admin_delete_pdf"),

    # Notes
    path("notes/", views.notes_list, name="notes_list"),
    path("notes/<int:note_id>/", views.note_detail, name="note_detail"),
    path("notes/create/", views.note_create, name="note_create"),

    # Flashcards
    path("flashcards/", views.flashcard_home, name="flashcard_home"),
    path("flashcards/<int:part_number>/session/", views.flashcard_session, name="flashcard_session"),
    path("flashcards/review/", views.flashcard_review, name="flashcard_review"),
    path("flashcards/api/count/", views.flashcard_available_count, name="flashcard_available_count"),

    # IRS Library
    path("irs-library/", views.irs_library, name="irs_library"),

    # Topic Resources — Student
    path("resources/<int:topic_id>/json/",      views.topic_resources_json,  name="topic_resources_json"),
    path("resources/<int:resource_id>/view/",   views.serve_topic_resource,  name="serve_topic_resource"),

    # Topic Resources — Admin CRUD
    path("admin/resources/",                             views.admin_resource_manager, name="admin_resource_manager"),
    path("admin/resources/<int:topic_id>/upload/",       views.admin_resource_upload,  name="admin_resource_upload"),
    path("admin/resources/<int:resource_id>/delete/",    views.admin_resource_delete,  name="admin_resource_delete"),
    path("admin/resources/<int:resource_id>/rename/",    views.admin_resource_rename,  name="admin_resource_rename"),
]
