from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
from xhtml2pdf import pisa
from django.contrib.auth import login as auth_login, authenticate
from django.core.mail import send_mail
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from .forms import StudentSignUpForm

from accounts.decorators import admin_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.forms import (
    ParentAddForm,
    ProfileUpdateForm,
    ProgramUpdateForm,
    StaffAddForm,
    StudentAddForm,
)
from accounts.models import Parent, Student, User
from core.models import Semester, Session
from course.models import Course

# ########################################################
# Utility Functions
# ########################################################


def render_to_pdf(template_name, context):
    """Render a given template to PDF format."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="profile.pdf"'
    template = render_to_string(template_name, context)
    pdf = pisa.CreatePDF(template, dest=response)
    if pdf.err:
        return HttpResponse("We had some problems generating the PDF")
    return response


# ########################################################
# Authentication and Registration
# ########################################################


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)


def register(request):
    if request.method == "POST":
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = False
            user.is_student = True
            user.save()
            
            # Ensure Student profile object exists
            if not Student.objects.filter(student=user).exists():
                Student.objects.create(student=user)
                
            messages.success(
                request,
                "Your account has been registered successfully! It is currently pending administrator approval."
            )
            return redirect("registration_success")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentSignUpForm()
    return render(request, "registration/register.html", {"form": form})


def registration_success(request):
    """View to show the success page securely after registration."""
    return render(request, "registration/register_success.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        if not email or not password:
            messages.error(request, "Please provide both email and password.")
            return render(request, "registration/login.html")
            
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # STRICT ADMIN RULE: Only this email is admin
            admin_email = "sonihiren233@gmail.com"
            if user.email == admin_email:
                user.is_staff = True
                user.is_superuser = True
                user.is_approved = True
                user.save()
                auth_login(request, user)
                messages.success(request, "Welcome, Admin!")
                return redirect("admin_panel")
            elif user.is_superuser or user.is_staff or user.is_lecturer or user.is_approved:
                auth_login(request, user)
                return redirect("ea_home")
            else:
                messages.error(
                    request,
                    "Your account registration is currently pending administrator approval. "
                    "You will be able to log in once an administrator approves your account."
                )
                return render(request, "registration/login.html")
        else:
            # Check if user password matched but user is unapproved
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user and existing_user.check_password(password) and not existing_user.is_approved:
                messages.error(
                    request,
                    "Your account registration is currently pending administrator approval. "
                    "You will be able to log in once an administrator approves your account."
                )
                return render(request, "registration/login.html")
            messages.error(request, "Invalid email or password.")
            
    return render(request, "registration/login.html")


def logout_view(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


# ########################################################
# Profile Views
# ########################################################


@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id, semester=current_semester
        )
        context["courses"] = courses
        return render(request, "accounts/profile.html", context)

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        parent = Parent.objects.filter(student=student).first()
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id, course__level=student.level
        )
        context.update(
            {
                "parent": parent,
                "courses": courses,
                "level": student.level,
            }
        )
        return render(request, "accounts/profile.html", context)

    # For superuser or other staff
    staff = User.objects.filter(is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()
    user = get_object_or_404(User, pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=user_id, semester=current_semester
        )
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id, course__level=student.level
        )
        context.update(
            {
                "user_type": "Student",
                "courses": courses,
                "student": student,
            }
        )
    else:
        context["user_type"] = "Superuser"

    if request.GET.get("download_pdf"):
        return render_to_pdf("pdf/profile_single.html", context)

    return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(request, "setting/admin_panel.html", {"title": "Admin Panel"})


# ########################################################
# Settings Views
# ########################################################


@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Upload profile picture to Supabase Storage if a new file was provided
            if 'picture' in request.FILES:
                try:
                    from ea_content.supabase_storage import upload_profile_picture
                    picture_file = request.FILES['picture']
                    public_url = upload_profile_picture(request.user.id, picture_file)
                    user.profile_picture_url = public_url
                except Exception as e:
                    # Fallback: save locally if Supabase upload fails
                    messages.warning(request, f"Profile picture saved locally (cloud upload failed).")
            
            user.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("edit_profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "setting/profile_info_change.html", {"form": form})


@login_required
def update_profile_picture(request):
    if request.method == "POST" and request.FILES.get("picture"):
        try:
            # First attempt: Supabase
            from ea_content.supabase_storage import upload_profile_picture
            picture_file = request.FILES['picture']
            public_url = upload_profile_picture(request.user.id, picture_file)
            request.user.profile_picture_url = public_url
            request.user.save()
            return JsonResponse({"success": True, "url": public_url})
        except Exception as e:
            # Fallback: Local storage
            request.user.picture = request.FILES['picture']
            request.user.save()
            return JsonResponse({"success": True, "url": request.user.picture.url})
    return JsonResponse({"success": False, "error": "No file uploaded"}, status=400)


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "setting/password_change.html", {"form": form})


# ########################################################
# Staff (Lecturer) Views
# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    if request.method == "POST":
        form = StaffAddForm(request.POST)
        if form.is_valid():
            lecturer = form.save()
            full_name = lecturer.get_full_name
            email = lecturer.email
            messages.success(
                request,
                f"Account for lecturer {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("lecturer_list")
    else:
        form = StaffAddForm()
    return render(
        request, "accounts/add_staff.html", {"title": "Add Lecturer", "form": form}
    )


@login_required
@admin_required
def edit_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=lecturer)
        if form.is_valid():
            form.save()
            full_name = lecturer.get_full_name
            messages.success(request, f"Lecturer {full_name} has been updated.")
            return redirect("lecturer_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=lecturer)
    return render(
        request, "accounts/edit_lecturer.html", {"title": "Edit Lecturer", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class LecturerFilterView(FilterView):
    filterset_class = LecturerFilter
    queryset = User.objects.filter(is_lecturer=True)
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lecturers"
        return context


@login_required
@admin_required
def render_lecturer_pdf_list(request):
    lecturers = User.objects.filter(is_lecturer=True)
    template_path = "pdf/lecturer_list.html"
    context = {"lecturers": lecturers}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="lecturers_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


# ########################################################
# Student Views
# ########################################################


@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            student = form.save()
            full_name = student.get_full_name
            email = student.email
            messages.success(
                request,
                f"Account for {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("student_list")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = StudentAddForm()
    return render(
        request, "accounts/add_student.html", {"title": "Add Student", "form": form}
    )


@login_required
@admin_required
def edit_student(request, pk):
    student_user = get_object_or_404(User, is_student=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=student_user)
        if form.is_valid():
            form.save()
            full_name = student_user.get_full_name
            messages.success(request, f"Student {full_name} has been updated.")
            return redirect("student_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=student_user)
    return render(
        request, "accounts/edit_student.html", {"title": "Edit Student", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    queryset = Student.objects.all()
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context


@login_required
@admin_required
def render_student_pdf_list(request):
    students = Student.objects.all()
    template_path = "pdf/student_list.html"
    context = {"students": students}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="students_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def approve_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    user = student.student
    user.is_approved = True
    user.save()
    full_name = user.get_full_name
    messages.success(request, f"Account for student {full_name} ({user.email}) has been approved!")
    return redirect("student_list")


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    full_name = student.student.get_full_name
    student.delete()
    messages.success(request, f"Student {full_name} has been deleted.")
    return redirect("student_list")


@login_required
@admin_required
def edit_student_program(request, pk):
    student = get_object_or_404(Student, student_id=pk)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ProgramUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            full_name = user.get_full_name
            messages.success(request, f"{full_name}'s program has been updated.")
            return redirect("profile_single", user_id=pk)
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProgramUpdateForm(instance=student)
    return render(
        request,
        "accounts/edit_student_program.html",
        {"title": "Edit Program", "form": form, "student": student},
    )


# ########################################################
# Parent Views
# ########################################################


@method_decorator([login_required, admin_required], name="dispatch")
class ParentAdd(CreateView):
    model = Parent
    form_class = ParentAddForm
    template_name = "accounts/parent_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Parent added successfully.")
        return super().form_valid(form)
