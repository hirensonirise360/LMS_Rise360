from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import date, timedelta

from ea_exam.models import EAPart
from ea_analytics.models import DomainAccuracy, StudyStreak, StudentEAProgress


@login_required
def analytics_dashboard(request):
    user = request.user
    parts = EAPart.objects.all()

    # Per-part stats
    part_stats = []
    for part in parts:
        domain_accs = DomainAccuracy.objects.filter(user=user, part_number=part.number)
        part_stats.append({
            "part": part,
            "sessions_count": 0,
            "avg_score": None,
            "best_score": None,
            "readiness": 0,
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

    return render(request, "ea_analytics/dashboard.html", {
        "title": "Analytics Dashboard",
        "part_stats": part_stats,
        "streak_days": streak_days,
        "total_questions": 0,
        "total_correct": 0,
        "overall_accuracy": 0,
        "total_sessions": 0,
    })
