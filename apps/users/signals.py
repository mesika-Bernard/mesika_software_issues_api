# apps/users/signals.py

from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from apps.projects.models import Project
from apps.features.models import Feature, ProjectFeature
from apps.issues.models import Issue


@receiver(post_migrate)
def create_roles_and_permissions(sender, **kwargs):
    """
    Create default roles (Admin, Project Manager, Developer, Tester)
    and assign relevant permissions for Projects, Features, ProjectFeatures, and Issues.
    """

    if sender.name not in ["apps.users", "apps.projects", "apps.features", "apps.issues"]:
        return

    # Groups
    groups = {
        "Admin": Group.objects.get_or_create(name="Admin")[0],
        "Project Manager": Group.objects.get_or_create(name="Project Manager")[0],
        "Developer": Group.objects.get_or_create(name="Developer")[0],
        "Tester": Group.objects.get_or_create(name="Tester")[0],
    }

    # Models
    models = {
        "Project": Project,
        "Feature": Feature,
        "ProjectFeature": ProjectFeature,
        "Issue": Issue,
    }

    # Permission mapping
    permissions_map = {
        "Admin": {
            Project: ["add", "view", "change", "delete"],
            Feature: ["add", "view", "change", "delete"],
            ProjectFeature: ["add", "view", "change", "delete"],
            Issue: ["add", "view", "change", "delete"],
        },
        "Project Manager": {
            Project: ["add", "view", "change", "delete"],
            Feature: ["add", "view", "change", "delete"],
            ProjectFeature: ["add", "view", "change", "delete"],
            Issue: ["add", "view"],  # PMs can add and view Issues
        },
        "Developer": {
            Project: ["view"],  # can list only
            Feature: ["add", "view", "change"],  # add + update + list
            ProjectFeature: ["add", "view", "change"],  # same as features
            Issue: ["add", "view", "change"],  # add + update + list
        },
        "Tester": {
            Project: ["view"],  # can list only
            Feature: ["view"],  # can only list features
            ProjectFeature: ["view"],  # can only list project features
            Issue: ["add", "view", "change"],  # add + update + list
        },
    }

    # Assign permissions
    for role, models_perms in permissions_map.items():
        group = groups[role]
        for model, actions in models_perms.items():
            content_type = ContentType.objects.get_for_model(model)
            for action in actions:
                codename = f"{action}_{model._meta.model_name}"
                try:
                    perm = Permission.objects.get(content_type=content_type, codename=codename)
                    group.permissions.add(perm)
                except Permission.DoesNotExist:
                    print(f"Permission {codename} not found for {model}")

