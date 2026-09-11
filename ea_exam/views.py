from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.db import models

from .models import EAPart, EADomain, EATopic, UserProgress, UserTopicReadStatus
from ea_analytics.models import StudentEAProgress, DomainAccuracy


def get_user_progress(user):
    """Get or create UserProgress for a user."""
    progress, _ = UserProgress.objects.get_or_create(user=user)
    return progress


@login_required
def ea_home(request):
    """RISE360 Institute Mission Control Home — Journey Map + Stats."""
    all_parts = list(EAPart.objects.prefetch_related("domains").order_by("number"))
    user_progress = get_user_progress(request.user)
    active_part = user_progress.active_part

    progress_qs = StudentEAProgress.objects.filter(user=request.user)
    progress_map = {p.part_number: p for p in progress_qs}

    part_progress = {}
    for part in all_parts:
        progress = progress_map.get(part.number)
        total_domains = len(part.domains.all())
        attempted = (progress.questions_attempted or 0) if progress else 0
        correct = (progress.questions_correct or 0) if progress else 0
        readiness = (progress.readiness_pct or 0) if progress else 0
        accuracy = round((correct / attempted) * 100) if attempted > 0 else 0

        part_progress[part.number] = {
            "progress": progress,
            "total_q": 0,
            "total_domains": total_domains,
            "attempted": attempted,
            "accuracy": accuracy,
            "readiness_pct": readiness,
            "attempted_pct": 0.0,
            "last_session": None,
        }

    active_pp = part_progress.get(active_part, {})
    total_attempted = active_pp.get("attempted", 0)
    overall_accuracy = active_pp.get("accuracy", 0)
    active_part_url = reverse("part_study", kwargs={"part_number": active_part})

    return render(request, "ea_exam/home.html", {
        "title": "RISE360 Institute — Student Dashboard",
        "all_parts": all_parts,
        "part_progress": part_progress,
        "total_attempted": total_attempted,
        "overall_accuracy": overall_accuracy,
        "total_attempted_combined": 0,
        "overall_accuracy_combined": 0,
        "streak": 0,
        "active_part": active_part,
        "active_part_url": active_part_url,
        "user_progress": user_progress,
    })


@login_required
def part_study(request, part_number):
    """
    Study Layout:
    - Top: Part Tabs
    - Left: Domain/Topic list
    - Right: Progress Stats
    """
    user_progress = get_user_progress(request.user)
    active_part = user_progress.active_part
    all_parts = EAPart.objects.all()

    if part_number > active_part:
        return redirect("part_study", part_number=active_part)
    current_part = get_object_or_404(EAPart, number=part_number)

    domains = current_part.domains.prefetch_related("topics").all()
    progress = StudentEAProgress.objects.filter(user=request.user, part_number=part_number).first()
    domain_accuracies = DomainAccuracy.objects.filter(user=request.user, part_number=part_number)
    domain_acc_map = {da.domain_name: da for da in domain_accuracies}

    unlocked_parts = [p for p in all_parts if p.number <= active_part]

    read_statuses = {
        rs.topic_id: rs.is_read
        for rs in request.user.topic_read_statuses.filter(topic__domain__part=current_part)
    }

    context = {
        "title": f"Learning Part {current_part.number}",
        "all_parts": all_parts,
        "unlocked_parts": unlocked_parts,
        "current_part": current_part,
        "domains": domains,
        "progress": progress,
        "total_questions": 0,
        "domain_acc_map": domain_acc_map,
        "flagged_count": 0,
        "topic_stats": {},
        "active_part": active_part,
        "read_statuses": read_statuses,
    }
    return render(request, "ea_exam/part_study.html", context)


@login_required
def part_detail(request, part_number):
    return redirect("part_study", part_number=part_number)


@login_required
@require_POST
def unlock_part(request, part_number):
    part = get_object_or_404(EAPart, number=part_number)
    user_progress = get_user_progress(request.user)
    user_progress.active_part = part_number
    user_progress.save()
    messages.success(request, f"Part {part_number} is now active!")
    return redirect("part_study", part_number=part_number)


@login_required
def start_practice(request, part_number):
    messages.info(request, "Practice mode is currently unavailable.")
    return redirect("part_study", part_number=part_number)


@login_required
def practice_question(request, session_id):
    return redirect("ea_home")


@login_required
@require_POST
def practice_submit_answer(request, session_id):
    return JsonResponse({"status": "error", "message": "MCQ practice disabled"}, status=400)


@login_required
def start_exam_simulation(request, part_number):
    messages.info(request, "Exam simulations are currently unavailable.")
    return redirect("part_study", part_number=part_number)


@login_required
def exam_interface(request, session_id):
    return redirect("ea_home")


@login_required
@require_POST
def exam_submit_answer(request, session_id):
    return JsonResponse({"status": "error", "message": "Exam mode disabled"}, status=400)


@login_required
@require_POST
def exam_toggle_flag(request, session_id):
    return JsonResponse({"status": "ok", "flagged": []})


@login_required
@require_POST
def exam_finish(request, session_id):
    return redirect("ea_home")


@login_required
def exam_get_question(request, session_id):
    return JsonResponse({"error": "Question mode disabled"}, status=400)


@login_required
def session_results(request, session_id):
    return redirect("ea_home")


@login_required
def exam_history(request):
    return redirect("ea_home")


@login_required
def get_practice_available_count(request):
    return JsonResponse({"count": 0})


@login_required
def get_topics_for_domain(request, domain_id):
    topics_qs = EATopic.objects.filter(domain_id=domain_id).order_by().values("name").annotate(min_id=models.Min("id")).order_by("name")
    topics = [{"id": t["min_id"], "name": t["name"]} for t in topics_qs]
    return JsonResponse({"topics": list(topics)})


@login_required
def get_topics_for_domains(request):
    domain_ids = request.GET.getlist("domain_id[]") or request.GET.getlist("domain_id")
    domain_ids = [d for d in domain_ids if d]
    if not domain_ids:
        return JsonResponse({"topics": []})

    topics_qs = (
        EATopic.objects
        .filter(domain_id__in=domain_ids)
        .order_by()
        .values("name", "domain_id")
        .annotate(min_id=models.Min("id"))
        .order_by("name")
    )
    seen_names = set()
    topics = []
    for t in topics_qs:
        if t["name"] not in seen_names:
            seen_names.add(t["name"])
            topics.append({"id": t["min_id"], "name": t["name"]})

    return JsonResponse({"topics": topics})


@login_required
@require_POST
def toggle_topic_read_status(request):
    topic_id = request.POST.get("topic_id")
    is_read = request.POST.get("is_read") == "true"
    if not topic_id:
        return JsonResponse({"status": "error", "message": "Missing topic ID"}, status=400)

    topic = get_object_or_404(EATopic, id=topic_id)
    rs, _ = UserTopicReadStatus.objects.update_or_create(
        user=request.user, topic=topic,
        defaults={"is_read": is_read}
    )

    progress = get_user_progress(request.user)
    progress.last_accessed_topic = topic
    progress.save(update_fields=["last_accessed_topic"])

    return JsonResponse({"status": "ok", "is_read": rs.is_read})


@login_required
def get_mcq_counts(request):
    return JsonResponse({
        "counts": {
            "all": 0,
            "unattempted": 0,
            "incorrect": 0,
            "flagged": 0,
            "attempted": 0,
            "notes": 0,
        }
    })


@login_required
@require_POST
def add_question_note(request):
    return JsonResponse({"status": "error", "message": "Notes disabled"}, status=400)
