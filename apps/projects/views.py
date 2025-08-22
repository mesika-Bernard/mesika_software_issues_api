from django.views.decorators.csrf import csrf_exempt
import json
from apps.projects.models import Project
from apps.users.models import CustomUser
from ..utils import format_response, validate_request_payload,require_token

@csrf_exempt
def create_project(request):
    """Create a new project (accessible to PMs/admins)."""
    if request.method != 'POST':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        data = json.loads(request.body)
        required_keys = ['name','slug','description']
        allowed_keys = {'name', 'slug','description', 'status', 'priority'}
        key_types = {
            'name': str, 
            'slug': str, 
            'status': str, 
            'description': str, 
            'priority': str
        }
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(
                message=error_message,
                data=[],
                http_status=400
            )

        # Validate status and priority values
        if 'status' in data and data['status'] not in dict(Project.ProjectStatus.choices):
            return format_response(
                message=f"Error : Invalid status. Must be one of {list(dict(Project.ProjectStatus.choices).keys())}",
                data=[],
                http_status=400
            )
        
        if 'priority' in data and data['priority'] not in dict(Project.PriorityLevel.choices):
            return format_response(
                message=f"Error : Invalid priority. Must be one of {list(dict(Project.PriorityLevel.choices).keys())}",
                data=[],
                http_status=400
            )

        # if not request.user.is_authenticated or not request.user.is_staff:
        #     return format_response(
        #         message="Error : Unauthorized access",
        #         data=[],
        #         http_status=403
        #     )
        
        if Project.objects.filter(name=data["name"]).exists():
            return format_response(
            message="Error : Project already exists",
            data=[],
            http_status=400
        )

        project = Project(
            name=data['name'],
            slug=data['slug'],
            description=data['description'],
            status=data.get('status', Project.ProjectStatus.PLANNING),
            priority=data.get('priority', Project.PriorityLevel.MEDIUM)
        )
        project.save()
        

        project_data = {
            'id': project.id,
                'name': project.name,
                'slug': project.slug,
                'description': project.description,
                # 'status_value': project.status,
                'status': project.get_status_display(),
                # 'priority_value': project.priority,
                'priority': project.get_priority_display(),
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
        }
        
        return format_response(
            message="Project created successfully",
            data=project_data,
            http_status=201
        )
    except json.JSONDecodeError:
        return format_response(
            message="Error : Invalid JSON",
            data=[],
            http_status=400
        )
    except Exception as e:
        return format_response(
            message=f"Error : {str(e)}",
            data=[],
            http_status=400
        )

@csrf_exempt
@require_token('Admin')
def list_projects(request):
    """List all projects (accessible to PMs/admins)."""
    if request.method != 'GET':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        # if not request.user.is_authenticated or not request.user.is_staff:
        #     return format_response(
        #         message="Error : Unauthorized access",
        #         data=[],
        #         http_status=403
        #     )

        projects = Project.objects.all()
        project_list = [
            {
                'id': project.id,
                'name': project.name,
                'slug': project.slug,
                'description': project.description,
                # 'status_value': project.status,
                'status': project.get_status_display(),
                # 'priority_value': project.priority,
                'priority': project.get_priority_display(),
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
            } for project in projects
        ]
        return format_response(
            message="Projects retrieved successfully",
            data=project_list,
            http_status=200
        )
    except Exception as e:
        return format_response(
            message=f"Error : {str(e)}",
            data=[],
            http_status=400
        )

@csrf_exempt
@require_token()
def get_project(request, project_id):
    """Get details of a specific project (accessible to PMs/admins)."""
    if request.method != 'GET':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        project = Project.objects.get(id=project_id)
        # if not request.user.is_staff and (not project.manager or project.manager != request.user):
        #     return format_response(
        #         message="Error : Unauthorized access",
        #         data=[],
        #         http_status=403
        #     )

        project_data = {
            'id': project.id,
            'name': project.name,
            'slug': project.slug,
            'description': project.description,
            'status_value': project.status,
            'status': project.get_status_display(),
            'priority_value': project.priority,
            'priority': project.get_priority_display(),
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
        }
        return format_response(
            message="Project retrieved successfully",
            data=project_data,
            http_status=200
        )
    except Project.DoesNotExist:
        return format_response(
            message="Error : Project not found",
            data=[],
            http_status=404
        )

@csrf_exempt
# @require_token
def update_project(request, project_id):
    """Update a project (accessible to PMs/admins)."""
    if request.method != 'POST':  # Using POST as per your preference for updates
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        project = Project.objects.get(id=project_id)
        # Remove manager authentication check since manager field is gone
        # if not request.user.is_staff:
        #     return format_response(
        #         message="Error : Unauthorized access",
        #         data=[],
        #         http_status=403
        #     )

        data = json.loads(request.body)
        allowed_keys = {'name', 'description', 'status', 'priority'}
        key_types = {
            'name': str, 
            'description': str, 
            'status': str, 
            'priority': str
        }
        is_valid, error_message = validate_request_payload(data, [], allowed_keys, key_types)
        if not is_valid:
            return format_response(
                message=error_message,
                data=[],
                http_status=400
            )

        # Validate status and priority values if provided
        if 'status' in data and data['status'] not in dict(Project.ProjectStatus.choices):
            return format_response(
                message=f"Error : Invalid status. Must be one of {list(dict(Project.ProjectStatus.choices).keys())}",
                data=[],
                http_status=400
            )
        
        if 'priority' in data and data['priority'] not in dict(Project.PriorityLevel.choices):
            return format_response(
                message=f"Error : Invalid priority. Must be one of {list(dict(Project.PriorityLevel.choices).keys())}",
                data=[],
                http_status=400
            )

        # Update the fields
        for key, value in data.items():
            if key in allowed_keys:
                setattr(project, key, value)
        project.save()

        # Match create_project response fields exactly
        project_data = {
            'id': project.id,
            'name': project.name,
            'slug': project.slug,
            'description': project.description,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
        }
        return format_response(
            message="Project updated successfully",
            data=project_data,
            http_status=200
        )
    except json.JSONDecodeError:
        return format_response(
            message="Error : Invalid JSON",
            data=[],
            http_status=400
        )
    except Project.DoesNotExist:
        return format_response(
            message="Error : Project not found",
            data=[],
            http_status=404
        )

@csrf_exempt
# @require_token
def delete_project(request, project_id):
    """Delete a project (accessible to PMs/admins)."""
    if request.method != 'POST':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        project = Project.objects.get(id=project_id)
        # if not request.user.is_staff and (not project.manager or project.manager != request.user):
        #     return format_response(
        #         message="Error : Unauthorized access",
        #         data=[],
        #         http_status=403
        #     )

        project.delete()
        return format_response(
            message="Project deleted successfully",
            data=[],
            http_status=200
        )
    except Project.DoesNotExist:
        return format_response(
            message="Error : Project not found",
            data=[],
            http_status=404
        )