import random
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.timezone import now
from django.db import models
from django.urls import reverse
from django.db.models import Count, Q
from .models import (
    EAPart, EADomain, EATopic, EAQuestion, EAExamSession, UserProgress,
    QuestionUserNote, UserTopicReadStatus,
)
from ea_analytics.models import StudentEAProgress, DomainAccuracy


def get_user_progress(user):
    """Get or create UserProgress for a user."""
    progress, _ = UserProgress.objects.get_or_create(user=user)
    return progress

@login_required
def ea_home(request):
    """RISE360 Institute Mission Control Home — Journey Map + Stats."""
    # Prefetch parts with their domains in one query (avoids part.domains.count() N+1)
    all_parts = list(EAPart.objects.prefetch_related("domains").order_by("number"))

    user_progress = get_user_progress(request.user)
    active_part = user_progress.active_part

    # ── Batch Query 1: All StudentEAProgress rows for this user ──
    progress_qs = StudentEAProgress.objects.filter(user=request.user)
    progress_map = {p.part_number: p for p in progress_qs}

    # ── Batch Query 2: Active question count per part ──
    q_counts = (
        EAQuestion.objects
        .filter(status="active")
        .values("part_id")
        .annotate(total=Count("id"))
    )
    q_count_map = {row["part_id"]: row["total"] for row in q_counts}

    # ── Batch Query 3: Last session per part ──
    # Fetch all sessions ordered by date, then keep only the latest per part in Python
    sessions_qs = (
        EAExamSession.objects
        .filter(user=request.user)
        .order_by("-started_at")
        .only("part_id", "started_at", "score", "completed", "mode")
    )
    last_session_map = {}
    for s in sessions_qs:
        if s.part_id not in last_session_map:
            last_session_map[s.part_id] = s

    # ── Build per-part progress dict ──
    part_progress = {}
    for part in all_parts:
        progress = progress_map.get(part.number)
        total_q = q_count_map.get(part.id, 0)
        total_domains = len(part.domains.all())  # uses prefetch cache — no extra query
        last_session = last_session_map.get(part.id)

        attempted = (progress.questions_attempted or 0) if progress else 0
        correct   = (progress.questions_correct   or 0) if progress else 0
        readiness = (progress.readiness_pct       or 0) if progress else 0

        accuracy     = round((correct / attempted) * 100) if attempted > 0 else 0
        attempted_pct = round((attempted / total_q) * 100, 1) if total_q > 0 else 0.0

        part_progress[part.number] = {
            "progress": progress,
            "total_q": total_q,
            "total_domains": total_domains,
            "attempted": attempted,
            "accuracy": accuracy,
            "readiness_pct": readiness,
            "attempted_pct": attempted_pct,
            "last_session": last_session,
        }

    # Stats filtered to active part only
    active_pp       = part_progress.get(active_part, {})
    total_attempted = active_pp.get("attempted", 0)
    overall_accuracy = active_pp.get("accuracy", 0)
    # Session count for the active part (already fetched)
    streak = sum(1 for s in sessions_qs if s.part_id == next(
        (p.id for p in all_parts if p.number == active_part), None
    ))

    active_part_url = reverse("part_study", kwargs={"part_number": active_part})

    total_attempted_combined = sum(p["attempted"] for p in part_progress.values())
    total_correct_combined   = sum(
        (p["progress"].questions_correct if p["progress"] else 0)
        for p in part_progress.values()
    )
    overall_accuracy_combined = (
        round((total_correct_combined / total_attempted_combined) * 100)
        if total_attempted_combined > 0 else 0
    )

    return render(request, "ea_exam/home.html", {
        "title": "RISE360 Institute — Student Dashboard",
        "all_parts": all_parts,
        "part_progress": part_progress,
        "total_attempted": total_attempted,
        "overall_accuracy": overall_accuracy,
        "total_attempted_combined": total_attempted_combined,
        "overall_accuracy_combined": overall_accuracy_combined,
        "streak": streak,
        "active_part": active_part,
        "active_part_url": active_part_url,
        "user_progress": user_progress,
    })


@login_required
def part_study(request, part_number):
    """
    Miles-style Study Layout:
    - Top: Part Tabs (only unlocked parts shown)
    - Left: Domain/Topic list
    - Right: Progress Stats
    """
    user_progress = get_user_progress(request.user)
    active_part = user_progress.active_part
    all_parts = EAPart.objects.all()
    # Enforce: user can only access parts <= their active_part
    if part_number > active_part:
        return redirect("part_study", part_number=active_part)
    current_part = get_object_or_404(EAPart, number=part_number)

    # Domains and Topics for the left navigation
    domains = current_part.domains.prefetch_related("topics").all()

    # Progress Data for the right panel
    progress = StudentEAProgress.objects.filter(user=request.user, part_number=part_number).first()

    # ── DB-level question totals per topic (single query) ──
    topic_totals_qs = (
        EAQuestion.objects
        .filter(part=current_part, status="active")
        .values("topic_id")
        .annotate(total=Count("id"))
    )
    topic_stats = {}
    for row in topic_totals_qs:
        tid = row["topic_id"]
        topic_stats[tid] = {
            "total": row["total"],
            "attempted_ids": set(),
            "correct_ids": set(),
            "flagged_ids": set(),
        }
    total_questions = sum(r["total"] for r in topic_totals_qs)

    # Build q_id → topic_id map + correct_choice_map in one query
    questions_in_part = EAQuestion.objects.filter(part=current_part, status="active").only(
        "id", "topic_id", "choice_1_correct", "choice_2_correct",
        "choice_3_correct", "choice_4_correct",
    )
    q_to_topic = {}
    correct_choice_map = {}
    for q in questions_in_part:
        q_to_topic[q.id] = q.topic_id
        correct_choice_map[q.id] = q.get_correct_choice_key()

    # Domain-level accuracy
    domain_accuracies = DomainAccuracy.objects.filter(user=request.user, part_number=part_number)
    domain_acc_map = {da.domain_name: da for da in domain_accuracies}

    # ── SINGLE-PASS over sessions ──
    total_flagged_ids = set()
    sessions = EAExamSession.objects.filter(
        user=request.user, part=current_part
    ).only("user_answers", "flagged_questions")

    for s in sessions:
        answered = s.user_answers or {}
        flagged  = s.flagged_questions or []

        for qid_str, cid in answered.items():
            qid = int(qid_str)
            tid = q_to_topic.get(qid)
            if tid and tid in topic_stats:
                topic_stats[tid]["attempted_ids"].add(qid)
                if cid == correct_choice_map.get(qid):
                    topic_stats[tid]["correct_ids"].add(qid)

        for qid in flagged:
            tid = q_to_topic.get(qid)
            if tid and tid in topic_stats:
                topic_stats[tid]["flagged_ids"].add(qid)
                total_flagged_ids.add(qid)

    # Final transform
    final_topic_stats = {}
    for tid, s in topic_stats.items():
        attempted = len(s["attempted_ids"])
        correct   = len(s["correct_ids"])
        final_topic_stats[tid] = {
            "attempted": attempted,
            "total": s["total"],
            "flagged": len(s["flagged_ids"]),
            "accuracy": round(correct / attempted * 100) if attempted > 0 else 0,
        }

    # Only show unlocked parts in tabs
    unlocked_parts = [p for p in all_parts if p.number <= active_part]

    # Read statuses for topics
    read_statuses = {
        rs.topic_id: rs.is_read
        for rs in request.user.topic_read_statuses.filter(topic__domain__part=current_part)
    }

    context = {
        "title": f"EA Part {current_part.number}",
        "all_parts": all_parts,
        "unlocked_parts": unlocked_parts,
        "current_part": current_part,
        "domains": domains,
        "progress": progress,
        "total_questions": total_questions,
        "domain_acc_map": domain_acc_map,
        "flagged_count": len(total_flagged_ids),
        "topic_stats": final_topic_stats,
        "active_part": active_part,
        "read_statuses": read_statuses,
    }
    return render(request, "ea_exam/part_study.html", context)


@login_required
def part_detail(request, part_number):
    """Legacy view — redirect to the new study layout."""
    return redirect("part_study", part_number=part_number)


# ──────────────────────────────────────────────
# SHARED PERFORMANCE HELPER
# ──────────────────────────────────────────────

def _get_user_session_sets(user, base_qs=None):
    """
    Single-pass computation of answered, flagged, and wrong question ID sets
    for a given user across all their sessions.

    Args:
        user: the authenticated user
        base_qs: optional EAQuestion queryset to scope correct_map to (avoids
                 loading all questions when only a subset is needed)

    Returns:
        (answered_ids: set, flagged_ids: set, wrong_ids: set, correct_map: dict)
    """
    # Build correct_map from the scoped queryset (or all active questions if None)
    if base_qs is None:
        base_qs = EAQuestion.objects.filter(status="active")

    # Fetch only the fields needed for correctness check
    questions = base_qs.only(
        "id", "choice_1_correct", "choice_2_correct",
        "choice_3_correct", "choice_4_correct",
    )
    correct_map = {q.id: q.get_correct_choice_key() for q in questions}

    answered_ids = set()
    flagged_ids  = set()

    # latest-answer tracking for wrong_ids (per question, use most recent session)
    latest_answer = {}  # {qid: cid}

    sessions = (
        EAExamSession.objects
        .filter(user=user)
        .only("user_answers", "flagged_questions", "started_at")
        .order_by("-started_at")   # newest first so first-seen = latest answer
    )

    for s in sessions:
        if s.user_answers:
            for qid_str, cid in s.user_answers.items():
                qid = int(qid_str)
                answered_ids.add(qid)
                if qid not in latest_answer:
                    latest_answer[qid] = cid   # first-seen = latest answer
        if s.flagged_questions:
            flagged_ids.update(s.flagged_questions)

    # Compute wrong_ids using latest answers
    wrong_ids = {
        qid for qid, cid in latest_answer.items()
        if qid in correct_map and cid != correct_map[qid]
    }

    return answered_ids, flagged_ids, wrong_ids, correct_map


# Part activation: confirm & activate the next part
@login_required
@require_POST
def unlock_part(request, part_number):
    """
    Called via POST to set a part as 'Active'.
    Any part can be activated at any time - sets it as the current active part.
    """
    part = get_object_or_404(EAPart, number=part_number)
    user_progress = get_user_progress(request.user)

    # Freely set any part as active
    user_progress.active_part = part_number
    user_progress.save()
    messages.success(request, f"Part {part_number} is now active!")

    return redirect("part_study", part_number=part_number)


# ──────────────────────────────────────────────
# PRACTICE MODE
# ──────────────────────────────────────────────

@login_required
def start_practice(request, part_number):
    """Create and start a practice session."""
    part = get_object_or_404(EAPart, number=part_number)

    if request.method == "POST" or (request.method == "GET" and (request.GET.getlist("domain_id") or request.GET.get("topic_id"))):
        # Handle both POST and direct GET launch
        data = request.POST if request.method == "POST" else request.GET
        # Support multi-domain selection (checkboxes send domain_id[] or multiple domain_id)
        domain_ids = data.getlist("domain_id[]")
        if not domain_ids:
            domain_ids = data.getlist("domain_id")
        domain_ids = [d for d in domain_ids if d]  # strip empty
        topic_ids = data.getlist("topic_id")
        select_type = data.get("select_type", "all")  # all | unattempted | incorrect | flagged | attempted | notes
        # Legacy support: if flagged_only was submitted directly
        if data.get("flagged_only") in ("on", "1", "true"):
            select_type = "flagged"

        num_questions = int(data.get("num_questions", 10))
        num_questions = min(max(num_questions, 1), 100)

        qs = EAQuestion.objects.filter(part=part, status="active")
        if domain_ids:
            qs = qs.filter(domain_id__in=domain_ids)

        clean_topic_ids = [t for t in topic_ids if t]
        if clean_topic_ids:
            qs = qs.filter(topic_id__in=clean_topic_ids)

        # ── Apply select_type filter using shared helper (single-pass) ──
        answered_ids, flagged_ids, wrong_ids, _ = _get_user_session_sets(request.user, qs)

        if select_type == "unattempted":
            qs = qs.exclude(id__in=answered_ids)
        elif select_type == "attempted":
            qs = qs.filter(id__in=answered_ids)
        elif select_type == "flagged":
            if not flagged_ids:
                messages.error(request, "You have no flagged questions.")
                return redirect("start_practice", part_number=part_number)
            qs = qs.filter(id__in=flagged_ids)
        elif select_type == "notes":
            qs = qs.filter(user_notes__user=request.user)
        elif select_type == "incorrect":
            if not wrong_ids:
                messages.error(request, "You have no incorrectly answered questions.")
                return redirect("start_practice", part_number=part_number)
            qs = qs.filter(id__in=wrong_ids)
        # 'all' needs no additional filter

        # Shuffle and pick
        questions = list(qs.order_by("?")[:num_questions])
        if not questions:
            messages.error(request, "No questions available for this selection.")
            return redirect("start_practice", part_number=part_number)

        q_ids = ",".join(str(q.id) for q in questions)

        # Save explicit domain/topic only if a single item was selected
        single_domain_id = domain_ids[0] if domain_ids and len(domain_ids) == 1 else None
        single_topic_id = clean_topic_ids[0] if clean_topic_ids and len(clean_topic_ids) == 1 else None

        session = EAExamSession.objects.create(
            user=request.user,
            part=part,
            domain_id=single_domain_id,
            topic_id=single_topic_id,
            mode="practice",
            num_questions=len(questions),
            time_limit_minutes=0,
            question_order=q_ids,
            question_list=q_ids,
        )

        # ── Determine view preference from mode selector ──
        # practice_mode: "practice" | "practice_exam_view" / "practice_exam" | "exam_view" / "exam"
        practice_mode = data.get("practice_mode") or data.get("mode", "practice")
        if practice_mode in ("practice_exam_view", "practice_exam"):
            # Vertical list, no feedback revealed until results page
            request.session[f"view_pref_{session.id}"] = "exam"
        elif practice_mode in ("exam_view", "exam"):
            # One question at a time, no feedback revealed until results page
            request.session[f"view_pref_{session.id}"] = "exam_view_single"
        else:
            # Standard practice: immediate feedback
            request.session[f"view_pref_{session.id}"] = "practice"

        request.session.modified = True
        return redirect("practice_question", session_id=session.id)

    domains = part.domains.all()
    return render(request, "ea_exam/start_practice.html", {
        "title": f"Practice – Part {part.number}",
        "part": part,
        "domains": domains,
    })


@login_required
def practice_question(request, session_id):
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user)

    if session.completed:
        return redirect("session_results", session_id=session.id)
        
    # Early submission check
    if request.GET.get("finish") == "1":
        session.compute_score()
        return redirect("session_results", session_id=session.id)

    # Get all questions in the session order
    all_qids = session.get_question_ids()
    questions_qs = EAQuestion.objects.filter(id__in=all_qids).prefetch_related("domain", "topic")
    q_map = {q.id: q for q in questions_qs}
    ordered_questions = [q_map[qid] for qid in all_qids if qid in q_map]

    if not ordered_questions:
        session.compute_score()
        return redirect("session_results", session_id=session.id)

    answered = session.user_answers or {}
    flagged = session.flagged_questions or []
    # Calculate statistics
    total = len(all_qids)
    answered_count = len(answered)
    
    # Pass existing notes for these questions
    user_notes = {n.question_id: n.content for n in QuestionUserNote.objects.filter(user=request.user, question__in=ordered_questions)}

    # Check view preference for "Practice (Exam View)"
    view_pref = request.session.get(f"view_pref_{session.id}", "practice")

    context = {
        "session": session,
        "questions": ordered_questions,
        "total": session.num_questions,
        "answered_count": len(answered),
        "answered": answered,
        "flagged": flagged,
        "user_notes": user_notes,
        "view_pref": view_pref,
    }
    return render(request, "ea_exam/practice_question.html", context)


@login_required
@require_POST
def practice_submit_answer(request, session_id):
    """AJAX: record answer in practice mode and return correctness + explanation."""
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user)
    if session.completed:
        return JsonResponse({"status": "error", "message": "Session already completed"}, status=400)

    data = request.POST
    question_id = int(data.get("question_id", 0))
    choice_id = data.get("choice_id", "")

    if not question_id or not choice_id:
        return JsonResponse({"status": "error", "message": "Missing data"}, status=400)

    question = get_object_or_404(EAQuestion, id=question_id)
    is_correct = question.check_answer(choice_id)
    session.record_answer(question_id, choice_id)
    
    # Return feedback for tutor mode
    correct_choice_key = question.get_correct_choice_key()
    
    return JsonResponse({
        "status": "ok",
        "is_correct": is_correct,
        "choice_id": choice_id,
        "correct_choice_id": correct_choice_key,
        "explanation": question.explanation or "",
        "choices_feedback": [
            {"id": c["id"], "text": c["choice_text"], "explanation": ""}
            for c in question.get_choices()
        ]
    })


# ──────────────────────────────────────────────
# EXAM SIMULATION MODE
# ──────────────────────────────────────────────

@login_required
def start_exam_simulation(request, part_number):
    """Start full 100-question Prometric-style exam simulation."""
    part = get_object_or_404(EAPart, number=part_number)

    if request.method == "POST":
        questions = list(
            EAQuestion.objects.filter(part=part, status="active").order_by("?")[:100]
        )
        if len(questions) < 10:
            messages.error(request, "Not enough questions available for a full exam. Please add more questions first.")
            return redirect("part_detail", part_number=part_number)

        q_ids = ",".join(str(q.id) for q in questions)
        session = EAExamSession.objects.create(
            user=request.user,
            part=part,
            mode="exam",
            num_questions=len(questions),
            time_limit_minutes=part.time_limit_minutes,
            question_order=q_ids,
            question_list=q_ids,
        )
        return redirect("exam_interface", session_id=session.id)

    return render(request, "ea_exam/start_exam.html", {
        "title": f"Exam Simulation – Part {part.number}",
        "part": part,
    })


@login_required
def exam_interface(request, session_id):
    """Full Prometric-clone exam UI."""
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user, mode="exam")

    if session.completed:
        return redirect("session_results", session_id=session.id)

    # Load all questions for the navigator
    all_ids = session.get_question_ids()
    questions_qs = EAQuestion.objects.filter(id__in=all_ids)
    q_map = {q.id: q for q in questions_qs}
    ordered_questions = [q_map[qid] for qid in all_ids if qid in q_map]

    answered = session.user_answers or {}
    flagged = session.flagged_questions or []

    # Current question index (from GET param)
    try:
        current_idx = int(request.GET.get("q", 1)) - 1
        current_idx = max(0, min(current_idx, len(ordered_questions) - 1))
    except (ValueError, TypeError):
        current_idx = 0

    current_question = ordered_questions[current_idx] if ordered_questions else None

    # Build navigator data
    navigator = []
    for i, q in enumerate(ordered_questions):
        qid = q.id
        state = "unanswered"
        if str(qid) in answered:
            state = "answered"
        if qid in flagged:
            state = "flagged"
        if i == current_idx:
            state = "current"
        navigator.append({"index": i + 1, "id": qid, "state": state})

    # Calculate elapsed vs remaining time
    elapsed_seconds = int((now() - session.started_at).total_seconds())
    total_seconds = session.time_limit_minutes * 60
    remaining_seconds = max(0, total_seconds - elapsed_seconds)

    return render(request, "ea_exam/exam_interface.html", {
        "session": session,
        "ordered_questions": ordered_questions,
        "current_question": current_question,
        "current_idx": current_idx,
        "navigator": navigator,
        "answered": answered,
        "flagged": flagged,
        "remaining_seconds": remaining_seconds,
        "total": len(ordered_questions),
    })


@login_required
@require_POST
def exam_submit_answer(request, session_id):
    """AJAX: record answer in exam mode."""
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user, mode="exam")
    if session.completed:
        return JsonResponse({"status": "error", "message": "Exam already completed"}, status=400)

    data = request.POST
    question_id = data.get("question_id")
    choice_id = data.get("choice_id")

    if question_id and choice_id:
        session.record_answer(int(question_id), choice_id)
        return JsonResponse({"status": "ok", "answered": len(session.user_answers)})
    return JsonResponse({"status": "error"}, status=400)


@login_required
@require_POST
def exam_toggle_flag(request, session_id):
    """AJAX: toggle flag on a question in either mode."""
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user)
    question_id = int(request.POST.get("question_id", 0))
    session.toggle_flag(question_id)
    return JsonResponse({"status": "ok", "flagged": session.flagged_questions})


@login_required
@require_POST
def exam_finish(request, session_id):
    """Submit the completed exam."""
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user, mode="exam")
    if not session.completed:
        session.compute_score()
    return redirect("session_results", session_id=session.id)


@login_required
def exam_get_question(request, session_id):
    """
    AJAX: Return question data for a given index in the exam session.
    Used by the exam interface JS to lazy-load questions on navigation
    instead of rendering all 100 questions as hidden DOM nodes on page load.
    """
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user, mode="exam")
    try:
        idx = int(request.GET.get("idx", 0))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid index"}, status=400)

    all_ids = session.get_question_ids()
    if idx < 0 or idx >= len(all_ids):
        return JsonResponse({"error": "Index out of range"}, status=400)

    qid = all_ids[idx]
    q = get_object_or_404(EAQuestion, id=qid)
    answered = session.user_answers or {}
    flagged  = session.flagged_questions or []

    return JsonResponse({
        "id": q.id,
        "idx": idx,
        "total": len(all_ids),
        "question_text": q.question_text,
        "is_flagged": q.id in flagged,
        "answered_choice": answered.get(str(q.id), None),
        "choices": [
            {"id": c["id"], "text": c["choice_text"]}
            for c in q.get_choices()
        ],
    })


# ──────────────────────────────────────────────
# RESULTS
# ──────────────────────────────────────────────

@login_required
def session_results(request, session_id):
    """Post-session results page (both practice and exam)."""
    session = get_object_or_404(EAExamSession, id=session_id, user=request.user)

    if not session.completed:
        session.compute_score()

    all_ids = session.get_question_ids()
    questions_qs = EAQuestion.objects.filter(id__in=all_ids).prefetch_related(
        "domain", "topic"
    )
    q_map = {q.id: q for q in questions_qs}
    ordered_questions = [q_map[qid] for qid in all_ids if qid in q_map]

    answered = session.user_answers or {}
    flagged = session.flagged_questions or []

    # Build per-question result data
    results = []
    domain_stats = {}
    for q in ordered_questions:
        chosen_id = answered.get(str(q.id))
        chosen_choice = None
        is_correct = False
        choices_list = q.get_choices()
        
        if chosen_id:
            matched = next((c for c in choices_list if c["id"] == chosen_id), None)
            if matched:
                chosen_choice = matched
                is_correct = matched["is_correct"]

        correct_choice = next((c for c in choices_list if c["is_correct"]), None)
        domain_name = q.domain.name if q.domain else "Unknown"
        if domain_name not in domain_stats:
            domain_stats[domain_name] = {"correct": 0, "total": 0}
        domain_stats[domain_name]["total"] += 1
        if is_correct:
            domain_stats[domain_name]["correct"] += 1

        results.append({
            "question": q,
            "chosen_choice": chosen_choice,
            "correct_choice": correct_choice,
            "is_correct": is_correct,
            "is_flagged": q.id in flagged,
            "was_answered": chosen_id is not None,
        })

    # Domain accuracy
    for dn, ds in domain_stats.items():
        ds["accuracy"] = round(ds["correct"] / ds["total"] * 100) if ds["total"] else 0

    # pass/fail for exam mode (scaled ~105/130 ≈ 80.77%)
    passed = None
    if session.mode == "exam":
        passed = (session.score or 0) >= 70  # approximate threshold

    return render(request, "ea_exam/session_results.html", {
        "title": "Session Results",
        "session": session,
        "results": results,
        "domain_stats": domain_stats,
        "passed": passed,
        "total": len(ordered_questions),
        "correct": session.total_correct,
        "wrong": len(ordered_questions) - session.total_correct,
        "unanswered": len(ordered_questions) - len(answered),
    })


@login_required
def exam_history(request):
    """View all past exam simulation attempts."""
    sessions = EAExamSession.objects.filter(
        user=request.user, completed=True
    ).select_related("part").order_by("-started_at")

    return render(request, "ea_exam/exam_history.html", {
        "title": "Exam History",
        "sessions": sessions,
    })


# ──────────────────────────────────────────────
# AJAX helpers
# ──────────────────────────────────────────────

@login_required
def get_practice_available_count(request):
    """AJAX: return exact count of available questions based on practice setup filters."""
    from .models import EAQuestion, EAExamSession

    part_id = request.GET.get("part_id")
    # Support multiple domain IDs from multi-select dropdown
    domain_ids = request.GET.getlist("domain_id[]")
    if not domain_ids:
        domain_ids = request.GET.getlist("domain_id")
    domain_ids = [d for d in domain_ids if d]
    topic_ids = request.GET.getlist("topic_id[]") or request.GET.getlist("topic_id")
    select_type = request.GET.get("select_type", "all")  # all|unattempted|incorrect|flagged|attempted|notes
    # Legacy flag support
    if request.GET.get("flagged_only") == "true":
        select_type = "flagged"

    if not part_id:
        return JsonResponse({"status": "error", "message": "Missing part ID"}, status=400)

    qs = EAQuestion.objects.filter(part_id=part_id, status="active")

    if domain_ids:
        qs = qs.filter(domain_id__in=domain_ids)

    clean_topic_ids = [t for t in topic_ids if t]
    if clean_topic_ids:
        qs = qs.filter(topic_id__in=clean_topic_ids)

    # ── Apply select_type filter using shared helper (single-pass) ──
    answered_ids, flagged_ids, wrong_ids, _ = _get_user_session_sets(request.user, qs)

    if select_type == "bulk":
        total_all = qs.count()
        total_attempted = qs.filter(id__in=answered_ids).count()
        total_unattempted = total_all - total_attempted
        total_flagged = qs.filter(id__in=flagged_ids).count()
        total_notes = qs.filter(user_notes__user=request.user).count()
        total_incorrect = qs.filter(id__in=wrong_ids).count()
        return JsonResponse({
            "counts": {
                "all": total_all,
                "unattempted": total_unattempted,
                "incorrect": total_incorrect,
                "flagged": total_flagged,
                "attempted": total_attempted,
                "notes": total_notes,
            }
        })

    if select_type == "unattempted":
        qs = qs.exclude(id__in=answered_ids)
    elif select_type == "attempted":
        qs = qs.filter(id__in=answered_ids)
    elif select_type == "flagged":
        qs = qs.filter(id__in=flagged_ids)
    elif select_type == "notes":
        qs = qs.filter(user_notes__user=request.user)
    elif select_type == "incorrect":
        qs = qs.filter(id__in=wrong_ids)
    # 'all' — no extra filter

    return JsonResponse({"count": qs.count()})

@login_required
def get_topics_for_domain(request, domain_id):
    """AJAX: return topics for a given domain (for practice setup form). Avoid duplicates."""
    from .models import EATopic
    # Clear any default ordering so only 'name' is in the GROUP BY
    topics_qs = EATopic.objects.filter(domain_id=domain_id).order_by().values("name").annotate(min_id=models.Min("id")).order_by("name")
    topics = [{"id": t["min_id"], "name": t["name"]} for t in topics_qs]
    return JsonResponse({"topics": list(topics)})


@login_required
def get_topics_for_domains(request):
    """AJAX: return deduplicated topics for one or more domain IDs (multi-select support)."""
    from .models import EATopic
    domain_ids = request.GET.getlist("domain_id[]")
    if not domain_ids:
        domain_ids = request.GET.getlist("domain_id")
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
    # Deduplicate by name (keep one entry per unique name)
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
    """AJAX: Toggle marked-as-read status for a topic."""
    from .models import UserTopicReadStatus, EATopic
    topic_id = request.POST.get("topic_id")
    is_read = request.POST.get("is_read") == "true"
    
    if not topic_id:
        return JsonResponse({"status": "error", "message": "Missing topic ID"}, status=400)
    
    topic = get_object_or_404(EATopic, id=topic_id)
    rs, created = UserTopicReadStatus.objects.update_or_create(
        user=request.user, topic=topic,
        defaults={"is_read": is_read}
    )
    
    # Also update last accessed topic on mark-as-read or any topic-level action
    progress = get_user_progress(request.user)
    progress.last_accessed_topic = topic
    progress.save(update_fields=["last_accessed_topic"])
    
    return JsonResponse({"status": "ok", "is_read": rs.is_read})

@login_required
def get_mcq_counts(request):
    """AJAX: return counts of available questions for various filters."""
    scope_type = request.GET.get("type")
    scope_id   = request.GET.get("id")
    user       = request.user

    base_qs = EAQuestion.objects.filter(status="active")
    if scope_type == "domain":
        base_qs = base_qs.filter(domain_id=scope_id)
    elif scope_type == "topic":
        base_qs = base_qs.filter(topic_id=scope_id)

    total_all = base_qs.count()

    # ── Single-pass helper replaces 2 separate session loops ──
    answered_ids, flagged_ids, wrong_ids, _ = _get_user_session_sets(user, base_qs)

    total_attempted   = base_qs.filter(id__in=answered_ids).count()
    total_unattempted = total_all - total_attempted
    total_flagged     = base_qs.filter(id__in=flagged_ids).count()
    total_notes       = base_qs.filter(user_notes__user=user).count()
    total_incorrect   = base_qs.filter(id__in=wrong_ids).count()

    return JsonResponse({
        "counts": {
            "all": total_all,
            "unattempted": total_unattempted,
            "incorrect": total_incorrect,
            "flagged": total_flagged,
            "attempted": total_attempted,
            "notes": total_notes,
        }
    })

@login_required
@require_POST
def add_question_note(request):
    """AJAX: Save or update a student's note for a specific question."""
    qid = request.POST.get("question_id")
    content = request.POST.get("content", "").strip()

    if not qid:
        return JsonResponse({"status": "error", "message": "Missing ID"}, status=400)

    note, created = QuestionUserNote.objects.update_or_create(
        user=request.user, question_id=qid,
        defaults={"content": content}
    )
    return JsonResponse({"status": "ok", "note": note.content})
