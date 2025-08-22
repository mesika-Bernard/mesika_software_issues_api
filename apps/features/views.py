from django.shortcuts import render

# Create your views here.
from django.views.decorators.csrf import csrf_exempt
import json
from apps.projects.models import Project
from apps.features.models import Feature, ProjectFeature
from ..utils import format_response, validate_request_payload

# Feature Management (Core Features)
@csrf_exempt
def create_feature(request):
    """Create a core feature definition"""
    if request.method != 'POST':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        data = json.loads(request.body)
        required_keys = ['name', 'description']
        allowed_keys = {'name', 'description'}
        key_types = {
            'name': str, 
            'description': str, 
        }
        
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(message=error_message, data=[], http_status=400)
        
        if Feature.objects.filter(name=data['name']).exists():
            return format_response(
                message="Error: Feature with this name already exists",
                data=[],
                http_status=400
            )
        
        feature = Feature(
            name=data['name'],
            description=data.get('description'),
        )
        feature.save()
        
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description,
            'created_at': feature.created_at.isoformat(),
            'updated_at': feature.updated_at.isoformat(),
        }
        
        return format_response(message="Feature created successfully", data=feature_data, http_status=201)
        
    except json.JSONDecodeError:
        return format_response(message="Error: Invalid JSON", data=[], http_status=400)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)
    
@csrf_exempt
def associate_feature_to_project(request):
    """Associate a feature with a project (add project-specific data)"""
    if request.method != 'POST':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        data = json.loads(request.body)
        required_keys = ['project_id', 'feature_id']
        allowed_keys = {'project_id', 'feature_id', 'status', 'priority', 'notes'}
        key_types = {
            'project_id': int, 
            'feature_id': int, 
            'status': str, 
            'priority': str,
            'notes': str
        }
        
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(message=error_message, data=[], http_status=400)
        
        try:
            project = Project.objects.get(id=data['project_id'])
            feature = Feature.objects.get(id=data['feature_id'])
        except (Project.DoesNotExist, Feature.DoesNotExist):
            return format_response(message="Error: Project or Feature not found", data=[], http_status=404)
        
        if ProjectFeature.objects.filter(project=project, feature=feature).exists():
            return format_response(
                message="Error: Feature already associated with this project",
                data=[],
                http_status=400
            )
        
        project_feature = ProjectFeature(
            project=project,
            feature=feature,
            status=data.get('status', Feature.FeatureStatus.PROPOSED),
            priority=data.get('priority', Feature.FeaturePriority.MEDIUM),
            notes=data.get('notes')
        )
        project_feature.save()
        
        response_data = {
            'id': project_feature.id,
            'project_id': project.id,
            'project_name': project.name,
            'feature_id': feature.id,
            'feature_name': feature.name,
            'status': project_feature.status,
            'priority': project_feature.priority,
            'notes': project_feature.notes,
            'created_at': project_feature.created_at.isoformat(),
        }
        
        return format_response(message="Feature associated with project successfully", data=response_data, http_status=201)
        
    except json.JSONDecodeError:
        return format_response(message="Error: Invalid JSON", data=[], http_status=400)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)


@csrf_exempt
def list_features_denormalized(request):
    """List features denormalized - each feature appears once per project association"""
    if request.method != 'GET':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        # Get all project-feature associations with related data
        project_features = ProjectFeature.objects.select_related(
            'feature', 'project'
        ).all()
        
        feature_list = []
        for association in project_features:
            # Create a separate entry for each feature-project combination
            feature_data = {
                'feature_id': association.feature.id,
                'project_id': association.project.id,
                'project_name': association.project.name,
                'feature_name': association.feature.name,
                'project_status': association.project.status.capitalize(),
                'feature_status': association.status.capitalize(),
                'feature_priority': association.priority.capitalize(),
                'notes': association.notes,
            }
            feature_list.append(feature_data)
        
        return format_response(
            message="Features listed with project associations (denormalized)",
            data=feature_list,
            http_status=200
        )
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)
    
    
@csrf_exempt
def update_feature(request, feature_id):
    """Update a core feature's name and description"""
    if request.method != 'POST':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        feature = Feature.objects.get(id=feature_id)
        data = json.loads(request.body)
        
        allowed_keys = {'name', 'description'}
        key_types = {
            'name': str, 
            'description': str,
        }
        
        is_valid, error_message = validate_request_payload(data, [], allowed_keys, key_types)
        if not is_valid:
            return format_response(message=error_message, data=[], http_status=400)
        
        # Check if name is being changed and if it conflicts with existing feature
        if 'name' in data and data['name'] != feature.name:
            if Feature.objects.filter(name=data['name']).exists():
                return format_response(
                    message="Error: Feature with this name already exists",
                    data=[],
                    http_status=400
                )
        
        # Update fields
        for key, value in data.items():
            if key in allowed_keys:
                setattr(feature, key, value)
        feature.save()
        
        feature_data = {
            'id': feature.id,
            'name': feature.name,
            'description': feature.description,
            'updated_at': feature.updated_at.isoformat(),
        }
        
        return format_response(message="Feature updated successfully", data=feature_data, http_status=200)
        
    except json.JSONDecodeError:
        return format_response(message="Error: Invalid JSON", data=[], http_status=400)
    except Feature.DoesNotExist:
        return format_response(message="Error: Feature not found", data=[], http_status=404)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)

@csrf_exempt
def update_project_feature(request, association_id):
    """Update project-specific feature data"""
    if request.method != 'POST':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        project_feature = ProjectFeature.objects.get(id=association_id)
        data = json.loads(request.body)
        
        allowed_keys = {'status', 'priority', 'notes'}
        key_types = {
            'status': str, 
            'priority': str,
            'notes': str
        }
        
        is_valid, error_message = validate_request_payload(data, [], allowed_keys, key_types)
        if not is_valid:
            return format_response(message=error_message, data=[], http_status=400)
        
        # Update fields
        for key, value in data.items():
            if key in allowed_keys:
                setattr(project_feature, key, value)
        project_feature.save()
        
        response_data = {
            'id': project_feature.id,
            'project_id': project_feature.project.id,
            'project_name': project_feature.project.name,
            'feature_id': project_feature.feature.id,
            'feature_name': project_feature.feature.name,
            'status': project_feature.status,
            'priority': project_feature.priority,
            'notes': project_feature.notes,
            'updated_at': project_feature.updated_at.isoformat(),
        }
        
        return format_response(message="Project feature updated successfully", data=response_data, http_status=200)
        
    except json.JSONDecodeError:
        return format_response(message="Error: Invalid JSON", data=[], http_status=400)
    except ProjectFeature.DoesNotExist:
        return format_response(message="Error: Project feature association not found", data=[], http_status=404)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)

@csrf_exempt
def list_features(request, project_id):
    """List all features for a specific project with their project-specific data"""
    if request.method != 'GET':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        project = Project.objects.get(id=project_id)
        project_features = ProjectFeature.objects.filter(project=project).select_related('feature')
        
        feature_list = [
            {
                'id': pf.id,
                'feature_id': pf.feature.id,
                'name': pf.feature.name,
                'description': pf.feature.description,
                'status': pf.status.capitalize(),
                'priority': pf.priority.capitalize(),
                'notes': pf.notes,
                'associated_at': pf.created_at.isoformat(),
                'updated_at': pf.updated_at.isoformat(),
            } for pf in project_features
        ]
        
        return format_response(
            message=f"Features for project '{project.name}' retrieved successfully",
            data=feature_list,
            http_status=200
        )
    except Project.DoesNotExist:
        return format_response(message="Error: Project not found", data=[], http_status=404)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)

@csrf_exempt
def list_all_features(request):
    """List all core features (without project associations)"""
    if request.method != 'GET':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        features = Feature.objects.all()
        feature_list = [
            {
                'id': feature.id,
                'name': feature.name,
                'description': feature.description,
                # 'project_count': feature.projects.count(),
                'created_at': feature.created_at.isoformat(),
                'updated_at': feature.updated_at.isoformat(),
            } for feature in features
        ]
        
        return format_response(message="All features retrieved successfully", data=feature_list, http_status=200)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)

@csrf_exempt
def remove_feature_from_project(request, association_id):
    """Remove a feature association from a project"""
    if request.method != 'POST':
        return format_response(message="Error: Method not allowed", data=[], http_status=405)
    
    try:
        project_feature = ProjectFeature.objects.get(id=association_id)
        project_feature.delete()
        
        return format_response(
            message="Feature removed from project successfully",
            data=[],
            http_status=200
        )
    except ProjectFeature.DoesNotExist:
        return format_response(message="Error: Project feature association not found", data=[], http_status=404)
    except Exception as e:
        return format_response(message=f"Error: {str(e)}", data=[], http_status=400)