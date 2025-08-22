from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from ..utils import format_response, validate_request_payload, require_token
import json
import secrets
import string

User = get_user_model()

@csrf_exempt
@require_token()
def users(request):
    """List all users or create a new user."""
    if request.method == 'GET':
        users = User.objects.all()
        data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'phone_number': user.phone_number,
            'gender': user.gender,
            'role' : user.groups.first().name if user.groups.exists() else None
        } for user in users]
        return format_response(
            message="Users retrieved successfully",
            data=data,
            http_status=200
        )

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            phone_number = data.get('phone_number', '')
            gender = data.get('gender', '')
            role = data.get('role', None) 
            
            # Generate password
            alphabet = string.ascii_letters + string.digits + string.punctuation
            password = ''.join(secrets.choice(alphabet) for _ in range(12))

            # Validation...
            required_keys = ['email', 'first_name', 'last_name', 'phone_number', 'gender','role']
            allowed_keys = {'email', 'first_name', 'last_name', 'phone_number', 'gender', 'role'}
            key_types = {
                'email': str,
                'first_name': str,
                'last_name': str,
                'phone_number': str,
                'gender': str,
                'role': (str, type(None)),
            }
            is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
            if not is_valid:
                return format_response(message=error_message, data=[], http_status=400)

            if not email:
                return format_response(message="Email is required", data=[], http_status=400)

            if User.objects.filter(username=email).exists():
                return format_response(message="User with this email already exists", data=[], http_status=400)

            user = User.objects.create_user(
                username=email,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                gender=gender
            )

            # Assign role if provided
            if role:
                try:
                    group = Group.objects.get(name=role)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    return format_response(message=f"Role '{role}' does not exist", data=[], http_status=400)
            else:
                return format_response(message="Please Select a role for the User", data=[], http_status=400)



            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'gender': user.gender,
                'role': role,
                'generated_password': password
            }

            return format_response(message="User created successfully", data=user_data, http_status=201)


        except json.JSONDecodeError:
            return format_response(message="Invalid JSON", data=[], http_status=400)

@csrf_exempt
# @require_token
def user_detail(request, user_id):
    """Retrieve or delete a user."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return format_response(
            message="User not found",
            data=[],
            http_status=404
        )

    if request.method == 'GET':
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'phone_number': user.phone_number,
            'gender': user.gender
        }
        return format_response(
            message="User retrieved successfully",
            data=data,
            http_status=200
        )

    elif request.method == 'DELETE':
        user.delete()
        return format_response(
            message="User deleted successfully",
            data=[],
            http_status=204
        )

    return format_response(message="Method not allowed", data=[], http_status=405)

@csrf_exempt
# @require_token
def update_user(request, user_id):
    """Update a user's details."""
    if request.method != 'POST':
        return format_response(
            message="Method not allowed",
            data=[],
            http_status=405 
        )

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return format_response(
            message="User not found",
            data=[],
            http_status=404
        )

    try:
        data = json.loads(request.body)
        user.email = data.get('email', user.email)
        user.username = data.get('email', user.username)  # Keep username in sync with email
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.gender = data.get('gender', user.gender)
        
        if data.get('password'):
            user.set_password(data['password'])
        
        user.save()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'phone_number': user.phone_number,
            'gender': user.gender
        }
        return format_response(
            message="User updated successfully",
            data=user_data,
            http_status=200
        )
    except json.JSONDecodeError:
        return format_response(
            message="Invalid JSON",
            data=[],
            http_status=400
        )