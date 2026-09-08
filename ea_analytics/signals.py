"""
Django signals: auto-update DomainAccuracy, StudentEAProgress,
and StudyStreak whenever an EAExamSession is completed.
"""
from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver

from ea_exam.models import EAExamSession, EAQuestion
from ea_analytics.models import DomainAccuracy, StudentEAProgress, StudyStreak


@receiver(post_save, sender=EAExamSession)
def update_analytics_on_session_complete(sender, instance, **kwargs):
    """Fires whenever an EAExamSession is saved. If it just became complete,
    recompute DomainAccuracy and StudentEAProgress for this user/part."""
    if not instance.completed:
        return

    user = instance.user
    part = instance.part
    answered = instance.user_answers or {}

    if not answered:
        return

    # Gather answered questions with domain info
    q_ids = [int(k) for k in answered.keys()]
    questions = EAQuestion.objects.filter(id__in=q_ids).select_related("domain")

    # --- Domain Accuracy ---
    domain_tally = {}  # domain_name -> {correct, total}
    for q in questions:
        dn = q.domain.name if q.domain else "Unknown"
        chosen_id = answered.get(str(q.id))
        is_correct = q.check_answer(chosen_id) if chosen_id else False
        if dn not in domain_tally:
            domain_tally[dn] = {"correct": 0, "total": 0}
        domain_tally[dn]["total"] += 1
        if is_correct:
            domain_tally[dn]["correct"] += 1

    for dn, stats in domain_tally.items():
        obj, _ = DomainAccuracy.objects.get_or_create(
            user=user, domain_name=dn, part_number=part.number
        )
        # Cumulative update
        obj.attempts += stats["total"]
        obj.correct += stats["correct"]
        obj.save()

    # --- StudentEAProgress: actual journey progress percentage ---
    # Progress = Unique questions attempted / Total active questions in part
    all_sessions = EAExamSession.objects.filter(user=user, part=part).only("user_answers")
    unique_qids = set()
    for s in all_sessions:
        if s.user_answers:
            unique_qids.update(int(k) for k in s.user_answers.keys())
            
    total_q = EAQuestion.objects.filter(part=part, status="active").count()
    readiness = round((len(unique_qids) / total_q) * 100, 1) if total_q > 0 else 0.0

    progress, _ = StudentEAProgress.objects.get_or_create(
        user=user, part_number=part.number
    )
    progress.questions_attempted += len(answered)
    progress.questions_correct += instance.total_correct
    progress.readiness_pct = readiness
    progress.save()

    # --- StudyStreak ---
    today = date.today()
    streak, _ = StudyStreak.objects.get_or_create(user=user, date=today)
    streak.questions_answered += len(answered)
    if instance.ended_at and instance.started_at:
        elapsed = int((instance.ended_at - instance.started_at).total_seconds() / 60)
        streak.minutes_studied += elapsed
    streak.save()
