"""Phase 3 ea_content models — eBooks, Notes, Flashcards (SRS), IRS Publications."""
from datetime import date, timedelta
import math

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from ea_exam.models import EAPart, EADomain, EATopic





# ────────────────────────────────────────────────
# Study Notes
# ────────────────────────────────────────────────

class EANote(models.Model):
    """Admin-uploaded or user-created study notes per topic."""
    title = models.CharField(max_length=200)
    part = models.ForeignKey(EAPart, on_delete=models.SET_NULL, null=True, blank=True)
    domain = models.ForeignKey(EADomain, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(EATopic, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    is_admin_note = models.BooleanField(default=True, help_text=_("Admin notes are visible to all students"))
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["part", "domain", "-created_at"]
        verbose_name = "EA Note"

    def __str__(self):
        return self.title


# ────────────────────────────────────────────────
# Flashcards with Spaced Repetition (SM-2 algorithm)
# ────────────────────────────────────────────────

class Flashcard(models.Model):
    part = models.ForeignKey(EAPart, on_delete=models.CASCADE, related_name="flashcards")
    domain = models.ForeignKey(EADomain, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(EATopic, on_delete=models.SET_NULL, null=True, blank=True)
    front = models.TextField(help_text=_("Question / term"))
    back = models.TextField(help_text=_("Answer / definition"))
    DIFFICULTY_CHOICES = (
        ("easy", _("Easy")),
        ("average", _("Average")),
        ("hard", _("Hard")),
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="average"
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["part", "domain"]
        verbose_name = "Flashcard"

    def __str__(self):
        return self.front[:80]


class FlashcardSRS(models.Model):
    """SM-2 spaced repetition state per user per card."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE)
    repetitions = models.PositiveSmallIntegerField(default=0)
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=1)
    next_review = models.DateField(default=date.today)
    last_quality = models.PositiveSmallIntegerField(default=3)  # 0-5

    class Meta:
        unique_together = ("user", "card")
        verbose_name = "Flashcard SRS State"

    def review(self, quality: int):
        """Apply SM-2 algorithm. quality: 0=blackout, 5=perfect."""
        quality = max(0, min(5, quality))
        self.last_quality = quality
        if quality < 3:
            self.repetitions = 0
            self.interval_days = 1
        else:
            if self.repetitions == 0:
                self.interval_days = 1
            elif self.repetitions == 1:
                self.interval_days = 6
            else:
                self.interval_days = round(self.interval_days * self.ease_factor)
            self.repetitions += 1
        self.ease_factor = max(
            1.3, self.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        )
        self.next_review = date.today() + timedelta(days=self.interval_days)
        self.save()



