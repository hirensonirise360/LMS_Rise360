from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.clickjacking import xframe_options_sameorigin
from . import supabase_storage

from ea_exam.models import EAPart, EADomain, EATopic
from .models import (
    EANote, Flashcard, FlashcardSRS
)


# ─── eBook Library (Direct PDF Access) ──────────────────────────────────────

@login_required
def ebook_library(request):
    """
    Shows a list of all published eBooks. 
    Users will click directly to view the PDF file.
    """
    parts = EAPart.objects.all()
    part_filter = request.GET.get("part")

    # Fetch topics that have ebook content
    ebooks_qs = EATopic.objects.filter(
        Q(pdf_file__gt="") | Q(ebook_external_url__gt="") | Q(supabase_pdf_path__gt="")
    ).select_related("domain__part").order_by("domain__part", "domain", "order")

    if part_filter:
        ebooks_qs = ebooks_qs.filter(domain__part__number=part_filter)

    return render(request, "ea_content/ebook_library.html", {
        "title": "eBook Library",
        "ebooks": ebooks_qs,
        "parts": parts,
        "part_filter": part_filter,
    })



# ─── Study Notes ─────────────────────────────────────────────────────────────

@login_required
def notes_list(request):
    parts = EAPart.objects.all()
    part_filter = request.GET.get("part")
    domain_filter = request.GET.get("domain")
    q = request.GET.get("q", "").strip()

    notes_qs = EANote.objects.filter(
        Q(is_admin_note=True) | Q(author=request.user)
    ).select_related("part", "domain", "topic")

    if part_filter:
        notes_qs = notes_qs.filter(part__number=part_filter)
    if domain_filter:
        notes_qs = notes_qs.filter(domain_id=domain_filter)
    if q:
        notes_qs = notes_qs.filter(Q(title__icontains=q) | Q(content__icontains=q))

    domains = EADomain.objects.all()
    return render(request, "ea_content/notes_list.html", {
        "title": "Study Notes",
        "notes": notes_qs,
        "parts": parts,
        "domains": domains,
        "part_filter": part_filter,
        "domain_filter": domain_filter,
        "q": q,
    })


@login_required
def note_detail(request, note_id):
    note = get_object_or_404(EANote, id=note_id)
    if not note.is_admin_note and note.author != request.user:
        messages.error(request, "Access denied.")
        return redirect("notes_list")
    return render(request, "ea_content/note_detail.html", {
        "title": note.title,
        "note": note,
    })


@login_required
def note_create(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        part_id = request.POST.get("part_id") or None
        domain_id = request.POST.get("domain_id") or None
        topic_id = request.POST.get("topic_id") or None
        if title and content:
            note = EANote.objects.create(
                title=title, content=content,
                part_id=part_id, domain_id=domain_id, topic_id=topic_id,
                is_admin_note=False, author=request.user,
            )
            messages.success(request, "Note created successfully.")
            return redirect("note_detail", note_id=note.id)
        messages.error(request, "Title and content are required.")

    parts = EAPart.objects.all()
    domains = EADomain.objects.all()
    return render(request, "ea_content/note_create.html", {
        "title": "Create Study Note",
        "parts": parts,
        "domains": domains,
    })


# ─── Flashcards ──────────────────────────────────────────────────────────────

@login_required
def flashcard_home(request):
    from ea_exam.models import UserProgress
    user_progress, _ = UserProgress.objects.get_or_create(user=request.user)

    if request.method == "POST" and "set_active_part" in request.POST:
        try:
            part_num = int(request.POST.get("set_active_part"))
            user_progress.active_part = part_num
            user_progress.save()
            messages.success(request, f"Part {part_num} is now active!")
        except ValueError:
            pass
        return redirect("flashcard_home")

    active_part_number = user_progress.active_part
    parts = list(EAPart.objects.all().prefetch_related("domains"))

    # Compute top dashboard stats for the active part
    cards_qs = Flashcard.objects.filter(part__number=active_part_number, is_published=True)
    today = date.today()
    total_cards = cards_qs.count()
    
    srs_overall = FlashcardSRS.objects.filter(user=request.user, card__part__number=active_part_number, card__is_published=True)
    attempted_cards = srs_overall.count()
    unattempted_cards = total_cards - attempted_cards
    due_count = srs_overall.filter(next_review__lte=today).count()
    mastered_cards = srs_overall.filter(last_quality__gte=4).count()
    
    attempted_pct = round((attempted_cards / total_cards) * 100) if total_cards > 0 else 0
    mastery_pct = round((mastered_cards / attempted_cards) * 100) if attempted_cards > 0 else 0

    # Calculate per-Part stats for all study cards
    for part in parts:
        part_cards = Flashcard.objects.filter(part=part, is_published=True)
        part.total_cards = part_cards.count()
        
        srs_qs = FlashcardSRS.objects.filter(user=request.user, card__part=part, card__is_published=True)
        part.attempted_cards = srs_qs.count()
        part.unattempted_cards = part.total_cards - part.attempted_cards
        part.due_count = srs_qs.filter(next_review__lte=today).count()
        part.mastered_cards = srs_qs.filter(last_quality__gte=4).count()
        
        part.attempted_pct = round((part.attempted_cards / part.total_cards) * 100) if part.total_cards > 0 else 0
        part.mastery_pct = round((part.mastered_cards / part.attempted_cards) * 100) if part.attempted_cards > 0 else 0

    return render(request, "ea_content/flashcard_home.html", {
        "title": "Flashcards",
        "parts": parts,
        "active_part": active_part_number,
        "total_cards": total_cards,
        "attempted_cards": attempted_cards,
        "unattempted_cards": unattempted_cards,
        "due_count": due_count,
        "mastered_cards": mastered_cards,
        "attempted_pct": attempted_pct,
        "mastery_pct": mastery_pct,
    })




@login_required
def flashcard_available_count(request):
    """AJAX view: return the count of flashcards matching selected filters."""
    part_number = request.GET.get("part_number")
    if not part_number:
        return JsonResponse({"count": 0})

    domain_ids = request.GET.getlist("domain_id[]") or request.GET.getlist("domain_id")
    if len(domain_ids) == 1 and "," in domain_ids[0]:
        domain_ids = domain_ids[0].split(",")
    domain_ids = [d for d in domain_ids if d]

    status = request.GET.get("status", "all")

    difficulties = request.GET.getlist("difficulty[]") or request.GET.getlist("difficulty")
    if len(difficulties) == 1 and "," in difficulties[0]:
        difficulties = difficulties[0].split(",")
    difficulties = [diff for diff in difficulties if diff]

    student_difficulties = request.GET.getlist("student_difficulty[]") or request.GET.getlist("student_difficulty")
    if len(student_difficulties) == 1 and "," in student_difficulties[0]:
        student_difficulties = student_difficulties[0].split(",")
    student_difficulties = [sd for sd in student_difficulties if sd]

    q = request.GET.get("q", "").strip()

    qs = Flashcard.objects.filter(part__number=part_number, is_published=True)
    if domain_ids:
        qs = qs.filter(domain_id__in=domain_ids)
    if difficulties:
        qs = qs.filter(difficulty__in=difficulties)
    if q:
        qs = qs.filter(Q(front__icontains=q) | Q(back__icontains=q))

    if status == "unattempted":
        seen_ids = FlashcardSRS.objects.filter(user=request.user, card__part__number=part_number).values_list("card_id", flat=True)
        qs = qs.exclude(id__in=seen_ids)
    elif status == "attempted":
        seen_ids = FlashcardSRS.objects.filter(user=request.user, card__part__number=part_number).values_list("card_id", flat=True)
        qs = qs.filter(id__in=seen_ids)

    if student_difficulties:
        qualities = []
        include_unselected = False
        for sd in student_difficulties:
            if sd == "easy":
                qualities.append(5)
            elif sd == "average":
                qualities.append(4)
            elif sd == "hard":
                qualities.extend([1, 2, 3])
            elif sd == "unselected":
                include_unselected = True

        matching_card_ids = set()
        if qualities:
            matching_card_ids.update(
                FlashcardSRS.objects.filter(
                    user=request.user, card__part__number=part_number, last_quality__in=qualities
                ).values_list("card_id", flat=True)
            )

        all_user_srs_card_ids = FlashcardSRS.objects.filter(
            user=request.user, card__part__number=part_number
        ).values_list("card_id", flat=True)

        if include_unselected:
            qs = qs.filter(Q(id__in=matching_card_ids) | ~Q(id__in=all_user_srs_card_ids))
        else:
            qs = qs.filter(id__in=matching_card_ids)

    return JsonResponse({"count": qs.count()})


@login_required
def flashcard_session(request, part_number):
    """Start/continue a filtered flashcard session."""
    part = get_object_or_404(EAPart, number=part_number)

    domain_ids = request.GET.getlist("domain_id[]") or request.GET.getlist("domain_id")
    if len(domain_ids) == 1 and "," in domain_ids[0]:
        domain_ids = domain_ids[0].split(",")
    domain_ids = [d for d in domain_ids if d]

    status = request.GET.get("status", "all")

    difficulties = request.GET.getlist("difficulty[]") or request.GET.getlist("difficulty")
    if len(difficulties) == 1 and "," in difficulties[0]:
        difficulties = difficulties[0].split(",")
    difficulties = [diff for diff in difficulties if diff]

    student_difficulties = request.GET.getlist("student_difficulty[]") or request.GET.getlist("student_difficulty")
    if len(student_difficulties) == 1 and "," in student_difficulties[0]:
        student_difficulties = student_difficulties[0].split(",")
    student_difficulties = [sd for sd in student_difficulties if sd]

    q = request.GET.get("q", "").strip()

    qs = Flashcard.objects.filter(part=part, is_published=True)
    if domain_ids:
        qs = qs.filter(domain_id__in=domain_ids)
    if difficulties:
        qs = qs.filter(difficulty__in=difficulties)
    if q:
        qs = qs.filter(Q(front__icontains=q) | Q(back__icontains=q))

    if status == "unattempted":
        seen_ids = FlashcardSRS.objects.filter(user=request.user, card__part=part).values_list("card_id", flat=True)
        qs = qs.exclude(id__in=seen_ids)
    elif status == "attempted":
        seen_ids = FlashcardSRS.objects.filter(user=request.user, card__part=part).values_list("card_id", flat=True)
        qs = qs.filter(id__in=seen_ids)

    if student_difficulties:
        qualities = []
        include_unselected = False
        for sd in student_difficulties:
            if sd == "easy":
                qualities.append(5)
            elif sd == "average":
                qualities.append(4)
            elif sd == "hard":
                qualities.extend([1, 2, 3])
            elif sd == "unselected":
                include_unselected = True

        matching_card_ids = set()
        if qualities:
            matching_card_ids.update(
                FlashcardSRS.objects.filter(
                    user=request.user, card__part=part, last_quality__in=qualities
                ).values_list("card_id", flat=True)
            )

        all_user_srs_card_ids = FlashcardSRS.objects.filter(
            user=request.user, card__part=part
        ).values_list("card_id", flat=True)

        if include_unselected:
            qs = qs.filter(Q(id__in=matching_card_ids) | ~Q(id__in=all_user_srs_card_ids))
        else:
            qs = qs.filter(id__in=matching_card_ids)

    # Shuffled session
    session_cards = list(qs.order_by("?"))

    limit = request.GET.get("limit")
    if limit and limit.isdigit():
        session_cards = session_cards[:int(limit)]

    if not session_cards:
        messages.info(request, "No flashcards found matching your selection.")
        return redirect("flashcard_home")

    return render(request, "ea_content/flashcard_session.html", {
        "title": f"Flashcards — Part {part.number}",
        "part": part,
        "cards": session_cards,
        "cards_json": [{"id": c.id, "front": c.front, "back": c.back} for c in session_cards],
    })


@login_required
@require_POST
def flashcard_review(request):
    """AJAX: record a flashcard review quality (0-5)."""
    card_id = int(request.POST.get("card_id"))
    quality = int(request.POST.get("quality", 3))
    card = get_object_or_404(Flashcard, id=card_id)
    srs, _ = FlashcardSRS.objects.get_or_create(
        user=request.user, card=card,
        defaults={"next_review": date.today()}
    )
    srs.review(quality)
    return JsonResponse({
        "status": "ok",
        "next_review": srs.next_review.isoformat(),
        "interval_days": srs.interval_days,
    })


# ─── IRS Publication Library ─────────────────────────────────────────────────

@login_required
def irs_library(request):
    q = request.GET.get("q", "").strip()
    part_filter = request.GET.get("part")
    featured_only = request.GET.get("featured") == "1"

    pubs = []

    parts = EAPart.objects.all()
    return render(request, "ea_content/irs_library.html", {
        "title": "IRS Publication Library",
        "pubs": pubs,
        "parts": parts,
        "q": q,
        "part_filter": part_filter,
        "featured_only": featured_only,
    })


# ─── Secure eBook PDF Viewer ─────────────────────────────────────────────────

@login_required
@xframe_options_sameorigin
def serve_ebook_pdf(request, topic_id):
    """
    Fetches the PDF bytes securely from Supabase using the service key
    and streams them to the client. This prevents direct public access
    and prevents the user from knowing the Supabase bucket URL.
    """
    topic = get_object_or_404(EATopic, id=topic_id)
    if not topic.supabase_pdf_path:
        raise Http404("eBook PDF not found.")
        
    try:
        pdf_bytes = supabase_storage.get_ebook_pdf_bytes(topic.supabase_pdf_path)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        # Security headers to prevent downloading/embedding elsewhere
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Sanitize filename (remove \r, \n, hidden chars) to prevent HTTP Header newline errors
        safe_name = "".join(c for c in topic.name if c.isprintable()).strip() 
        
        # Support download query param
        download_mode = request.GET.get("download", "0") == "1"
        if download_mode:
            response['Content-Disposition'] = f'attachment; filename="{safe_name}.pdf"'
        else:
            response['Content-Disposition'] = f'inline; filename="{safe_name}.pdf"'
            
        return response
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Supabase Download Error:\n{traceback_str}")
        return HttpResponseForbidden(f"Unable to retrieve eBook. Exact error: {e}")


# ─── Custom Admin: eBook Manager ─────────────────────────────────────────────

@staff_member_required
def admin_ebook_manager(request):
    """
    A dashboard for admins to easily upload/replace/delete PDFs per topic.
    """
    # Get all topics grouped by part and domain
    topics = EATopic.objects.select_related("domain", "domain__part").order_by("domain__part__number", "domain__order", "order")
    
    return render(request, "ea_content/admin_ebook_manager.html", {
        "title": "eBook Configuration Manager",
        "topics": topics,
    })

@staff_member_required
@require_POST
def admin_upload_pdf(request, topic_id):
    topic = get_object_or_404(EATopic, id=topic_id)
    file_obj = request.FILES.get("pdf_file")
    if not file_obj:
        messages.error(request, "No file selected.")
        return redirect("admin_ebook_manager")
        
    if not file_obj.name.lower().endswith(".pdf"):
        messages.error(request, "Must be a PDF file.")
        return redirect("admin_ebook_manager")
        
    try:
        # Upload to supabase
        path = supabase_storage.upload_ebook_pdf(topic_id, file_obj)
        topic.supabase_pdf_path = path
        topic.save()
        messages.success(request, f"Successfully uploaded PDF for {topic.name}")
    except Exception as e:
        messages.error(request, f"Failed to upload: {str(e)}")
        
    return redirect("admin_ebook_manager")

@staff_member_required
@require_POST
def admin_delete_pdf(request, topic_id):
    topic = get_object_or_404(EATopic, id=topic_id)
    if topic.supabase_pdf_path:
        success = supabase_storage.delete_ebook_pdf(topic.supabase_pdf_path)
        if success:
            topic.supabase_pdf_path = ""
            topic.save()
            messages.success(request, f"Deleted PDF for {topic.name}")
        else:
            messages.error(request, "Failed to delete from storage.")
            
    return redirect("admin_ebook_manager")

