from django.urls import path, include

from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from .views import (
    profile,
    profile_single,
    admin_panel,
    profile_update,
    update_profile_picture,
    change_password,
    LecturerFilterView,
    StudentListView,
    staff_add_view,
    edit_staff,
    delete_staff,
    student_add_view,
    edit_student,
    delete_student,
    approve_student,
    edit_student_program,
    ParentAdd,
    validate_username,
    register,
    login_view,
    logout_view,
    render_lecturer_pdf_list,
    render_student_pdf_list,
    registration_success,
)
from .views_content_manager import (
    learning_manager,
    module_add, module_save, module_delete,
    domain_add, domain_save, domain_delete,
    topic_editor, topic_editor_new, topic_save, topic_create, topic_delete,
)


# from .forms import EmailValidationOnForgotPassword


urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register, name="register"),
    path("register/success/", registration_success, name="registration_success"),
    path("logout/", logout_view, name="logout"),
    path("admin_panel/", admin_panel, name="admin_panel"),
    path("profile/", profile, name="profile"),
    path("profile/<int:user_id>/detail/", profile_single, name="profile_single"),
    path("setting/", profile_update, name="edit_profile"),
    path("setting/picture/", update_profile_picture, name="update_profile_picture"),
    path("change_password/", change_password, name="change_password"),
    path("lecturers/", LecturerFilterView.as_view(), name="lecturer_list"),
    path("lecturer/add/", staff_add_view, name="add_lecturer"),
    path("staff/<int:pk>/edit/", edit_staff, name="staff_edit"),
    path("lecturers/<int:pk>/delete/", delete_staff, name="lecturer_delete"),
    path("students/", StudentListView.as_view(), name="student_list"),
    path("student/add/", student_add_view, name="add_student"),
    path("student/<int:pk>/edit/", edit_student, name="student_edit"),
    path("students/<int:pk>/approve/", approve_student, name="student_approve"),
    path("students/<int:pk>/delete/", delete_student, name="student_delete"),
    path(
        "edit_student_program/<int:pk>/",
        edit_student_program,
        name="student_program_edit",
    ),
    path("parents/add/", ParentAdd.as_view(), name="add_parent"),
    path("ajax/validate-username/", validate_username, name="validate_username"),
    # paths to pdf
    path(
        "create_lecturers_pdf_list/", render_lecturer_pdf_list, name="lecturer_list_pdf"
    ),  # new
    path(
        "create_students_pdf_list/", render_student_pdf_list, name="student_list_pdf"
    ),  # new
    # path('add-student/', StudentAddView.as_view(), name='add_student'),
    # path('programs/course/delete/<int:pk>/', course_delete, name='delete_course'),
    # Setting urls
    # path('profile/<int:pk>/edit/', profileUpdateView, name='edit_profile'),
    # path('profile/<int:pk>/change-password/', changePasswordView, name='change_password'),
    path("password-reset/", PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        extra_email_context={'protocol': 'https'},
    ),
         name='password_reset'),
    path("password-reset/done/", PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ),
         name='password_reset_done'),
    path("password-reset-confirm/<uidb64>/<token>/", PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ),
         name='password_reset_confirm'),
    path("password-reset-complete/", PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ),
         name='password_reset_complete'),

    # ── Learning Content Manager ──────────────────────────────────────────────
    path("learning-manager/",                              learning_manager,    name="learning_manager"),
    # Module CRUD
    path("learning-manager/module/add/",                  module_add,          name="lm_module_add"),
    path("learning-manager/module/<int:pk>/save/",        module_save,         name="lm_module_save"),
    path("learning-manager/module/<int:pk>/delete/",      module_delete,       name="lm_module_delete"),
    # Domain CRUD
    path("learning-manager/domain/add/",                  domain_add,          name="lm_domain_add"),
    path("learning-manager/domain/<int:pk>/save/",        domain_save,         name="lm_domain_save"),
    path("learning-manager/domain/<int:pk>/delete/",      domain_delete,       name="lm_domain_delete"),
    # Topic CRUD
    path("learning-manager/topic/new/",                   topic_editor_new,    name="lm_topic_new"),
    path("learning-manager/topic/create/",                topic_create,        name="lm_topic_create"),
    path("learning-manager/topic/<int:pk>/",              topic_editor,        name="lm_topic_editor"),
    path("learning-manager/topic/<int:pk>/save/",         topic_save,          name="lm_topic_save"),
    path("learning-manager/topic/<int:pk>/delete/",       topic_delete,        name="lm_topic_delete"),
]

