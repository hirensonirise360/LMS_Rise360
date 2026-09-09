import json
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


# ──────────────────────────────────────────────
# EA DOMAIN TAXONOMY
# ──────────────────────────────────────────────

class EAPart(models.Model):
    number = models.PositiveSmallIntegerField(unique=True, help_text=_("Display order / module number"))
    name = models.CharField(max_length=200, help_text=_("Topic name, e.g. MS Excel, Bookkeeping, Canadian Taxation"))
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["number"]
        verbose_name = _("Learning Topic / Module")
        verbose_name_plural = _("Learning Topics / Modules")

    def __str__(self):
        return f"{self.name}"


class EADomain(models.Model):
    part = models.ForeignKey(EAPart, on_delete=models.CASCADE, related_name="domains")
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["part", "order"]
        verbose_name = _("EA Domain")
        verbose_name_plural = _("EA Domains")

    def __str__(self):
        return f"{self.part} › {self.name}"


class EATopic(models.Model):
    domain = models.ForeignKey(EADomain, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    # Content fields consolidated into Topic
    video_file = models.FileField(upload_to="ea_videos/", null=True, blank=True)
    video_external_url = models.URLField(blank=True, help_text=_("YouTube/Vimeo link"))
    pdf_file = models.FileField(upload_to="ea_ebooks/", null=True, blank=True)
    supabase_pdf_path = models.CharField(max_length=500, blank=True, default="", help_text=_("Path in Supabase 'ea-ebooks' private bucket"))

    class Meta:
        ordering = ["domain", "order"]
        verbose_name = _("EA Topic")
        verbose_name_plural = _("EA Topics")

    def __str__(self):
        return f"{self.domain.part.number}.{self.domain.name} › {self.name}"


# ──────────────────────────────────────────────
# QUESTION BANK
# ──────────────────────────────────────────────

DIFFICULTY_CHOICES = (
    ("easy", _("Easy")),
    ("medium", _("Medium")),
    ("hard", _("Hard")),
)

STATUS_CHOICES = (
    ("active", _("Active")),
    ("retired", _("Retired")),
    ("review", _("Under Review")),
)


class EAQuestion(models.Model):
    part = models.ForeignKey(EAPart, on_delete=models.CASCADE, related_name="questions")
    domain = models.ForeignKey(EADomain, on_delete=models.CASCADE, related_name="questions")
    topic = models.ForeignKey(EATopic, on_delete=models.SET_NULL, null=True, blank=True, related_name="questions")

    question_text = models.TextField(help_text=_("The main question text"))
    explanation = models.TextField(blank=True, help_text=_("Why is the correct answer correct?"))

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    choice_1 = models.CharField(max_length=500, verbose_name=_("Choice 1"), default="", blank=True)
    choice_2 = models.CharField(max_length=500, verbose_name=_("Choice 2"), default="", blank=True)
    choice_3 = models.CharField(max_length=500, verbose_name=_("Choice 3"), default="", blank=True)
    choice_4 = models.CharField(max_length=500, verbose_name=_("Choice 4"), default="", blank=True)
    
    choice_1_correct = models.BooleanField(default=False, verbose_name=_("Choice 1 Correct"))
    choice_2_correct = models.BooleanField(default=False, verbose_name=_("Choice 2 Correct"))
    choice_3_correct = models.BooleanField(default=False, verbose_name=_("Choice 3 Correct"))
    choice_4_correct = models.BooleanField(default=False, verbose_name=_("Choice 4 Correct"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["part", "domain", "difficulty"]
        verbose_name = _("EA Question")
        verbose_name_plural = _("EA Questions")
        indexes = [
            models.Index(fields=["part", "status"]),
            models.Index(fields=["domain", "status"]),
            models.Index(fields=["topic", "status"]),
        ]

    def __str__(self):
        return f"[{self.part.number}|{self.difficulty}] {self.question_text[:80]}"

    def get_choices(self):
        """Returns a list of choice dictionaries mimicking the old EAChoice objects."""
        return [
            {"id": "choice1", "choice_text": self.choice_1, "is_correct": self.choice_1_correct},
            {"id": "choice2", "choice_text": self.choice_2, "is_correct": self.choice_2_correct},
            {"id": "choice3", "choice_text": self.choice_3, "is_correct": self.choice_3_correct},
            {"id": "choice4", "choice_text": self.choice_4, "is_correct": self.choice_4_correct},
        ]

    def get_correct_choice_key(self):
        """Returns the correct choice ID string key."""
        if self.choice_1_correct:
            return "choice1"
        if self.choice_2_correct:
            return "choice2"
        if self.choice_3_correct:
            return "choice3"
        if self.choice_4_correct:
            return "choice4"
        return "choice1"  # fallback

    def get_correct_choice(self):
        # Compatibility helper returning a fake choice object
        key = self.get_correct_choice_key()
        text = getattr(self, key.replace("choice", "choice_"))
        return type("FakeChoice", (object,), {"id": key, "choice_text": text, "is_correct": True, "explanation": ""})

    def check_answer(self, choice_key):
        """Checks if the passed choice key ('choice1', 'choice2', etc.) is correct."""
        choice_str = str(choice_key).strip().lower()
        if choice_str == "choice1":
            return self.choice_1_correct
        if choice_str == "choice2":
            return self.choice_2_correct
        if choice_str == "choice3":
            return self.choice_3_correct
        if choice_str == "choice4":
            return self.choice_4_correct
        return False


# ──────────────────────────────────────────────
# EXAM SESSION
# ──────────────────────────────────────────────

SESSION_MODE = (
    ("practice", _("Practice Mode")),
    ("exam", _("Exam Simulation")),
)


class EAExamSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ea_sessions"
    )
    part = models.ForeignKey(EAPart, on_delete=models.CASCADE)
    domain = models.ForeignKey(EADomain, on_delete=models.SET_NULL, null=True, blank=True,
                                help_text=_("If set, practice is filtered to this domain"))
    topic = models.ForeignKey(EATopic, on_delete=models.SET_NULL, null=True, blank=True)

    mode = models.CharField(max_length=10, choices=SESSION_MODE, default="practice")

    # question order stored as comma-separated IDs
    question_order = models.TextField(default="")
    question_list = models.TextField(default="")  # remaining to answer

    user_answers = models.JSONField(default=dict)   # {question_id: choice_id}
    flagged_questions = models.JSONField(default=list)  # [question_id, ...]

    num_questions = models.PositiveSmallIntegerField(default=10)
    time_limit_minutes = models.PositiveSmallIntegerField(default=30)

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    score = models.FloatField(null=True, blank=True)  # percentage
    total_correct = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = _("EA Exam Session")
        verbose_name_plural = _("EA Exam Sessions")
        indexes = [
            models.Index(fields=["user", "part"]),
            models.Index(fields=["user", "-started_at"]),
        ]

    def __str__(self):
        return f"{self.user} | {self.get_mode_display()} | {self.part} | {self.started_at.strftime('%Y-%m-%d')}"

    def get_question_ids(self):
        return [int(q) for q in self.question_order.split(",") if q.strip()]

    def get_remaining_ids(self):
        return [int(q) for q in self.question_list.split(",") if q.strip()]

    def get_next_question(self):
        remaining = self.get_remaining_ids()
        if not remaining:
            return None
        return EAQuestion.objects.filter(id=remaining[0]).first()

    def advance_question(self):
        remaining = self.get_remaining_ids()
        if remaining:
            remaining.pop(0)
            self.question_list = ",".join(map(str, remaining))
            self.save(update_fields=["question_list"])

    def record_answer(self, question_id, choice_id):
        answers = self.user_answers or {}
        answers[str(question_id)] = choice_id
        self.user_answers = answers
        self.save(update_fields=["user_answers"])

    def toggle_flag(self, question_id):
        flagged = self.flagged_questions or []
        if question_id in flagged:
            flagged.remove(question_id)
        else:
            flagged.append(question_id)
        self.flagged_questions = flagged
        self.save(update_fields=["flagged_questions"])

    def compute_score(self):
        """Compute and persist score. Call on session completion."""
        correct = 0
        questions = EAQuestion.objects.filter(id__in=self.get_question_ids())
        q_map = {q.id: q for q in questions}
        for qid_str, cid in self.user_answers.items():
            q = q_map.get(int(qid_str))
            if q and q.check_answer(cid):
                correct += 1
        total = len(self.get_question_ids())
        self.total_correct = correct
        self.score = (correct / total * 100) if total > 0 else 0
        self.completed = True
        self.ended_at = now()
        self.save(update_fields=["total_correct", "score", "completed", "ended_at"])
        return self.score

    @property
    def elapsed_minutes(self):
        if self.ended_at:
            return int((self.ended_at - self.started_at).total_seconds() / 60)
        return int((now() - self.started_at).total_seconds() / 60)

    @property
    def progress_pct(self):
        total = len(self.get_question_ids())
        answered = len(self.user_answers)
        return int(answered / total * 100) if total else 0


# ──────────────────────────────────────────────
# USER PERSONALIZATION
# ──────────────────────────────────────────────

class QuestionUserNote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="question_notes"
    )
    question = models.ForeignKey(
        "EAQuestion", on_delete=models.CASCADE, related_name="user_notes"
    )
    content = models.TextField(help_text=_("Student's personal note for this question"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "question")
        verbose_name = _("Question User Note")
        verbose_name_plural = _("Question User Notes")

    def __str__(self):
        return f"Note by {self.user} on Q{self.question.id}"


# ──────────────────────────────────────────────
# USER PROGRESS / PART GATING
# ──────────────────────────────────────────────

class UserProgress(models.Model):
    """
    Tracks which EA Part the student is currently active on.
    active_part: the highest unlocked part (1, 2, or 3).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ea_user_progress"
    )
    active_part = models.PositiveSmallIntegerField(default=1)
    last_accessed_topic = models.ForeignKey(
        "EATopic", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = _("User Progress")

    def __str__(self):
        return f"{self.user} — Active Part: {self.active_part}"

    def is_part_complete(self, part_number):
        """
        Returns True if average domain accuracy for the given part >= 80%.
        Uses DomainAccuracy records from ea_analytics.
        Falls back to False if no data exists.
        """
        from ea_analytics.models import DomainAccuracy
        domain_accs = DomainAccuracy.objects.filter(
            user=self.user, part_number=part_number
        )
        if not domain_accs.exists():
            return False
        total_accuracy = sum(da.accuracy_pct for da in domain_accs)
        avg_accuracy = total_accuracy / domain_accs.count()
        return avg_accuracy >= 80


class UserTopicReadStatus(models.Model):
    """
    Tracks if a user has marked a specific topic as 'Read' or 'Completed'.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_read_statuses"
    )
    topic = models.ForeignKey(EATopic, on_delete=models.CASCADE, related_name="read_statuses")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "topic")
        verbose_name = _("User Topic Read Status")
        verbose_name_plural = _("User Topic Read Statuses")
        indexes = [
            models.Index(fields=["user", "topic"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.topic.name} - Read: {self.is_read}"
