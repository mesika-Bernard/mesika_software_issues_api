from django.db import models
from apps.projects.models import Project

class Feature(models.Model):
    """Core feature definition (independent of projects)"""
    class FeatureStatus(models.TextChoices):
        PROPOSED = 'proposed', 'Proposed'
        PLANNED = 'planned', 'Planned'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        REJECTED = 'rejected', 'Rejected'

    class FeaturePriority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    # Core feature data (shared across all projects)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Projects that use this feature (through ProjectFeature)
    projects = models.ManyToManyField(
        Project,
        through='ProjectFeature',
        through_fields=('feature', 'project'),
        related_name='features',
        blank=True
    )
    
    # Global/default status and priority (optional)
    default_status = models.CharField(
        max_length=20,
        choices=FeatureStatus.choices,
        default=FeatureStatus.PROPOSED
    )
    default_priority = models.CharField(
        max_length=20,
        choices=FeaturePriority.choices,
        default=FeaturePriority.MEDIUM
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class ProjectFeature(models.Model):
    """Association table with project-specific feature data"""
    project = models.ForeignKey(Project, on_delete=models.RESTRICT)
    feature = models.ForeignKey(Feature, on_delete=models.RESTRICT)
    
    # Project-specific status and priority
    status = models.CharField(
        max_length=20,
        choices=Feature.FeatureStatus.choices,
        default=Feature.FeatureStatus.PROPOSED
    )
    priority = models.CharField(
        max_length=20,
        choices=Feature.FeaturePriority.choices,
        default=Feature.FeaturePriority.MEDIUM
    )
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.feature.name}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['project', 'feature']