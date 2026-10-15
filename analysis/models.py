from django.conf import settings
from django.db import models


class JobAnalysis(models.Model):

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_analyses"
    )

    cv = models.ForeignKey(
        "cvs.CV",
         on_delete=models.SET_NULL,
    null=True,
    blank=True,
        related_name="job_analyses"
    )

    company_name = models.CharField(
        max_length=255
    )

    job_title = models.CharField(
        max_length=255
    )

    job_description = models.TextField()

    match_score = models.PositiveIntegerField(
        default=0
    )

    match_label = models.CharField(
        max_length=50,
        blank=True
    )

    matched_skills = models.JSONField(
        default=list,
        blank=True
    )

    missing_skills = models.JSONField(
        default=list,
        blank=True
    )

    strengths = models.JSONField(
        default=list,
        blank=True
    )

    weak_areas = models.JSONField(
        default=list,
        blank=True
    )

    detailed_analysis = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )

    error_message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "job_analysis"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} - {self.job_title}"