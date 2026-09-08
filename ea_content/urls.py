from django.urls import path
from . import views

urlpatterns = [
    # eBooks
    path("", views.ebook_library, name="ebook_library"),
    path("ebooks/view/<int:topic_id>/", views.serve_ebook_pdf, name="serve_ebook_pdf"),
    
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
]
