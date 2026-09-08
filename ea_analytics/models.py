from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class StudentEAProgress(models.Model):
    """Overall per-part readiness tracking."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ea_progress")
    part_number = models.PositiveSmallIntegerField()  # 1, 2, 3
    questions_attempted = models.PositiveIntegerField(default=0)
    questions_correct = models.PositiveIntegerField(default=0)
    readiness_pct = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "part_number")

    @property
    def accuracy(self):
        if self.questions_attempted == 0:
            return 0
        return round(self.questions_correct / self.questions_attempted * 100, 1)


class DomainAccuracy(models.Model):
    """Per-domain accuracy tracking."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="domain_accuracy")
    domain_name = models.CharField(max_length=200)
    part_number = models.PositiveSmallIntegerField()
    attempts = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "domain_name", "part_number")

    @property
    def accuracy_pct(self):
        return round(self.correct / self.attempts * 100) if self.attempts else 0

    @property
    def readiness_color(self):
        a = self.accuracy_pct
        if a >= 70:
            return "success"
        elif a >= 50:
            return "warning"
        return "danger"


class StudyStreak(models.Model):
    """Daily activity log for streak tracking."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_streaks")
    date = models.DateField()
    questions_answered = models.PositiveIntegerField(default=0)
    minutes_studied = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]
