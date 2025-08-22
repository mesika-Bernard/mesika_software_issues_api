from django.views.decorators.csrf import csrf_exempt
import json
from apps.projects.models import Project
from apps.features.models import ProjectFeature
from .models import Issue
from ..utils import format_response, validate_request_payload


@csrf_exempt
def create_issue(request):
    """Create a new issue (linked to a project)."""
    if request.method != 'POST':
        return format_response("Error: Method not allowed", [], 405)

    try:
        data = json.loads(request.body)
        required_keys = ['title', 'project', 'description']
        allowed_keys = {'title', 'project', 'project_feature', 'priority', 'category', 'status', 'description'}
        key_types = {
            'title': str,
            'project': int,
            'project_feature': int,
            'priority': str,
            'category': str,
            'status': str,
            'description': str
        }

        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(error_message, [], 400)

        # Validate project exists
        try:
            project = Project.objects.get(id=data['project'])
        except Project.DoesNotExist:
            return format_response("Error: Project not found", [], 404)

        # Validate optional project_feature
        project_feature = None
        if 'project_feature' in data:
            try:
                project_feature = ProjectFeature.objects.get(id=data['project_feature'])
            except ProjectFeature.DoesNotExist:
                return format_response("Error: Project feature not found", [], 404)

        # Validate choice fields
        if 'priority' in data and data['priority'] not in dict(Issue.Priority.choices):
            return format_response(
                f"Error: Invalid priority. Must be one of {list(dict(Issue.Priority.choices).keys())}", [], 400
            )
        if 'category' in data and data['category'] not in dict(Issue.Category.choices):
            return format_response(
                f"Error: Invalid category. Must be one of {list(dict(Issue.Category.choices).keys())}", [], 400
            )
        if 'status' in data and data['status'] not in dict(Issue.Status.choices):
            return format_response(
                f"Error: Invalid status. Must be one of {list(dict(Issue.Status.choices).keys())}", [], 400
            )

        issue = Issue.objects.create(
            title=data['title'],
            project=project,
            project_feature=project_feature,
            priority=data.get('priority', Issue.Priority.MEDIUM),
            category=data.get('category', Issue.Category.BUG),
            status=data.get('status', Issue.Status.OPEN),
            description=data['description']
        )

        issue_data = {
            'id': issue.id,
            'title': issue.title,
            'project': issue.project.id,
            'project_feature': issue.project_feature.id if issue.project_feature else None,
            'priority': issue.get_priority_display(),
            'category': issue.get_category_display(),
            'status': issue.get_status_display(),
            'description': issue.description,
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat(),
        }
        return format_response("Issue created successfully", issue_data, 201)

    except json.JSONDecodeError:
        return format_response("Error: Invalid JSON", [], 400)
    except Exception as e:
        return format_response(f"Error: {str(e)}", [], 400)


@csrf_exempt
def list_issues(request):
    """List all issues."""
    if request.method != 'GET':
        return format_response("Error: Method not allowed", [], 405)

    try:
        issues = Issue.objects.all()
        issue_list = [
            {
                'id': issue.id,
                'title': issue.title,
                'project': issue.project.name,
                'project_feature': issue.project_feature.feature.name if issue.project_feature else None,
                'priority': issue.get_priority_display(),
                'category': issue.get_category_display(),
                'status': issue.get_status_display(),
                'description': issue.description,
                'created_at': issue.created_at.isoformat(),
                'updated_at': issue.updated_at.isoformat(),
            } for issue in issues
        ]
        return format_response("Issues retrieved successfully", issue_list, 200)
    except Exception as e:
        return format_response(f"Error: {str(e)}", [], 400)


@csrf_exempt
def get_issue(request, issue_id):
    """Get details of a specific issue."""
    if request.method != 'GET':
        return format_response("Error: Method not allowed", [], 405)

    try:
        issue = Issue.objects.get(id=issue_id)
        issue_data = {
            'id': issue.id,
            'title': issue.title,
            'project': issue.project.id,
            'project_feature': issue.project_feature.id if issue.project_feature else None,
            'priority': issue.get_priority_display(),
            'category': issue.get_category_display(),
            'status': issue.get_status_display(),
            'description': issue.description,
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat(),
        }
        return format_response("Issue retrieved successfully", issue_data, 200)
    except Issue.DoesNotExist:
        return format_response("Error: Issue not found", [], 404)


@csrf_exempt
def update_issue(request, issue_id):
    """Update an issue."""
    if request.method != 'POST':
        return format_response("Error: Method not allowed", [], 405)

    try:
        issue = Issue.objects.get(id=issue_id)
        data = json.loads(request.body)
        allowed_keys = {'title', 'priority', 'category', 'status', 'description'}
        key_types = {
            'title': str,
            'priority': str,
            'category': str,
            'status': str,
            'description': str
        }

        is_valid, error_message = validate_request_payload(data, [], allowed_keys, key_types)
        if not is_valid:
            return format_response(error_message, [], 400)


        if 'priority' in data and data['priority'] not in dict(Issue.Priority.choices):
            return format_response(
                f"Error: Invalid priority. Must be one of {list(dict(Issue.Priority.choices).keys())}", [], 400
            )

        if 'category' in data and data['category'] not in dict(Issue.Category.choices):
            return format_response(
                f"Error: Invalid category. Must be one of {list(dict(Issue.Category.choices).keys())}", [], 400
            )

        if 'status' in data and data['status'] not in dict(Issue.Status.choices):
            return format_response(
                f"Error: Invalid status. Must be one of {list(dict(Issue.Status.choices).keys())}", [], 400
            )

        for key, value in data.items():
            if key in allowed_keys and key not in ['project', 'project_feature']:
                setattr(issue, key, value)

        issue.save()

        issue_data = {
            'id': issue.id,
            'title': issue.title,
            'project': issue.project.id,
            'project_feature': issue.project_feature.id if issue.project_feature else None,
            'priority': issue.get_priority_display(),
            'category': issue.get_category_display(),
            'status': issue.get_status_display(),
            'description': issue.description,
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat(),
        }
        return format_response("Issue updated successfully", issue_data, 200)

    except json.JSONDecodeError:
        return format_response("Error: Invalid JSON", [], 400)
    except Issue.DoesNotExist:
        return format_response("Error: Issue not found", [], 404)


@csrf_exempt
def delete_issue(request, issue_id):
    """Delete an issue."""
    if request.method != 'POST':
        return format_response("Error: Method not allowed", [], 405)

    try:
        issue = Issue.objects.get(id=issue_id)
        issue.delete()
        return format_response("Issue deleted successfully", [], 200)
    except Issue.DoesNotExist:
        return format_response("Error: Issue not found", [], 404)
