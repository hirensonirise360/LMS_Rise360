from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Avg, Sum, Count
from datetime import date, timedelta

from ea_exam.models import EAPart, EAExamSession, EAQuestion
from ea_analytics.models import DomainAccuracy, StudyStreak, StudentEAProgress


@login_required
def analytics_dashboard(request):
    user = request.user
    parts = EAPart.objects.all()

    # Per-part stats from completed sessions
    part_stats = []
    for part in parts:
        sessions = EAExamSession.objects.filter(user=user, part=part, completed=True)
        avg_score = sessions.aggregate(a=Avg("score"))["a"]
        best_score = sessions.order_by("-score").first()
        domain_accs = DomainAccuracy.objects.filter(user=user, part_number=part.number)

        part_stats.append({
            "part": part,
            "sessions_count": sessions.count(),
            "avg_score": round(avg_score, 1) if avg_score else None,
            "best_score": round(best_score.score, 1) if best_score else None,
            "readiness": round(avg_score, 1) if avg_score else 0,
            "domain_accs": domain_accs,
        })

    # Study streak — last 7 days
    today = date.today()
    streak_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        streak = StudyStreak.objects.filter(user=user, date=d).first()
        streak_days.append({
            "date": d,
            "active": streak is not None,
            "questions": streak.questions_answered if streak else 0,
        })

    # Totals
    all_sessions = EAExamSession.objects.filter(user=user, completed=True)
    total_questions = sum(s.num_questions for s in all_sessions)
    total_correct = sum(s.total_correct for s in all_sessions)
    overall_accuracy = round(total_correct / total_questions * 100, 1) if total_questions else 0

    return render(request, "ea_analytics/dashboard.html", {
        "title": "EA Analytics Dashboard",
        "part_stats": part_stats,
        "streak_days": streak_days,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_accuracy": overall_accuracy,
        "total_sessions": all_sessions.count(),
    })
