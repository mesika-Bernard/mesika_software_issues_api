from django.db import models
from apps.projects.models import Project
from apps.features.models import ProjectFeature

class Issue(models.Model):
    class Priority(models.TextChoices):
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    class Category(models.TextChoices):
        BUG = 'bug', 'Bug'
        FEATURE_REQUEST = 'feature_request', 'Feature Request'
        IMPROVEMENT = 'improvement', 'Improvement'
        # Removed "Task"

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_REVIEW = 'in_review', 'In Review'
        CLOSED = 'closed', 'Closed'
        REOPENED = 'reopened', 'Reopened'

    title = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='issues')
    project_feature = models.ForeignKey(
        ProjectFeature,
        on_delete=models.CASCADE,
        related_name='issues',
        null=True,
        blank=True
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.BUG
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (#{self.id})"

    class Meta:
        ordering = ['-created_at']
