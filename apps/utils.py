from django.http import JsonResponse
import jwt
import time
from issue_tracker_api import settings
import secrets
import uuid
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth import get_user_model
import datetime
import redis

User = get_user_model()

# Initialize Redis client
REDIS_CLIENT = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

def get_user_role(user):
    """
    Get the user's role based on their assigned group.
    Prioritizes roles: Admin > Project Manager > Developer > Tester.
    Returns 'None' if no group is assigned.
    """
    groups = user.groups.all()
    if not groups:
        return "None"
    
    # Define role priority
    role_priority = ["Admin", "Project Manager", "Developer", "Tester"]
    user_groups = [group.name for group in groups]
    
    # Return the highest-priority role
    for role in role_priority:
        if role in user_groups:
            return role
    return user_groups[0]  # Fallback to first group if not in priority list

def generate_tokens(user):
    """
    Generate access and refresh tokens for a user, including their role.
    """
    role = get_user_role(user)
    
    access_payload = {
        'user_id': user.id,
        'role': role,
        'exp': int(time.time()) + settings.JWT_ACCESS_TOKEN_LIFETIME,
        'iat': int(time.time()),
        'type': 'access'
    }
    access_token = jwt.encode(access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    refresh_payload = {
        'user_id': user.id,
        'role': role,
        'exp': int(time.time()) + settings.JWT_REFRESH_TOKEN_LIFETIME,
        'iat': int(time.time()),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }

def require_token(allowed_roles=None):
    """
    Decorator to require a valid JWT access token with a specific role.
    Attaches the authenticated user to the request if valid.
    
    Args:
        allowed_roles (list, optional): List of roles allowed to access the endpoint.
            If None, any role is allowed (but token must still be valid).
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return format_response(
                    message="Error: Authorization header required",
                    data=[],
                    http_status=400
                )

            if not auth_header.startswith('Bearer '):
                return format_response(
                    message="Error: Invalid Authorization header format",
                    data=[],
                    http_status=400
                )

            token = auth_header[len('Bearer '):].strip()
            # Check Redis blacklist
            if REDIS_CLIENT.get(f"blacklist_{token}"):
                return format_response(
                    message="Error: Invalid Authorization Token",
                    data=[],
                    http_status=401
                )

            try:
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
                if payload['type'] != 'access':
                    return format_response(
                        message="Error: Token is not an access token",
                        data=[],
                        http_status=401
                    )

                # Check role as first step of authorization
                user_role = payload.get('role', 'None')
                if allowed_roles is not None and user_role not in allowed_roles:
                    return format_response(
                        message=f"Error: Access restricted",
                        data=[],
                        http_status=403
                    )

                # user_id = payload['user_id']
                # request.user = User.objects.get(id=user_id)
            except jwt.ExpiredSignatureError:
                return format_response(
                    message="Error: Token has expired",
                    data=[],
                    http_status=401
                )
            except (jwt.InvalidTokenError, User.DoesNotExist):
                return format_response(
                    message="Error: Invalid or expired token",
                    data=[],
                    http_status=401
                )

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def blacklist_token(token):
    """
    Add token to Redis blacklist with expiration matching its original expiry.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        expiry = datetime.datetime.fromtimestamp(payload['exp'])
        timeout = max(0, int((expiry - datetime.datetime.utcnow()).total_seconds()))
        REDIS_CLIENT.setex(f"blacklist_{token}", timeout, "true")
    except jwt.InvalidTokenError:
        # If token is invalid, blacklist it indefinitely
        REDIS_CLIENT.set(f"blacklist_{token}", "true")

def generate_otp():
    """
    Generate a random 6-digit OTP.
    """
    return str(secrets.randbelow(900000) + 100000)  # 100000–999999

def store_otp(user_id, otp, temp_token):
    """
    Store OTP with user_id and expiration time (5 minutes) in Redis using temp_token as key.
    """
    expires_at = int(time.time()) + 300  # 5 minutes in seconds
    otp_data = {
        'user_id': user_id,
        'otp': otp,
        'expires_at': expires_at
    }
    REDIS_CLIENT.setex(f"otp_{temp_token}", 300, json.dumps(otp_data))

def validate_otp(temp_token, otp):
    """
    Validate OTP against stored value in Redis using temp_token and check expiration.
    Returns (is_valid, user_id, error_message).
    """
    otp_data_json = REDIS_CLIENT.get(f"otp_{temp_token}")
    if not otp_data_json:
        return False, None, "Error: Invalid temporary token"
    
    otp_data = json.loads(otp_data_json)
    if int(time.time()) > otp_data['expires_at']:
        REDIS_CLIENT.delete(f"otp_{temp_token}")
        return False, None, "Error: OTP has expired"
    
    if otp != otp_data['otp']:
        return False, None, "Error: Invalid OTP"
    
    user_id = otp_data['user_id']
    REDIS_CLIENT.delete(f"otp_{temp_token}")  # Remove OTP after validation
    return True, user_id, ""

def format_response(message, data=None, http_status=200):
    """
    Format API response in the structure: { "message": "", "data": [], "status": "" }.
    """
    if data is None:
        data = []
    response = {
        "message": message,
        "data": data,
        "status": http_status
    }
    return JsonResponse(response, status=http_status)

def validate_request_payload(data, required_keys, allowed_keys=None, key_types=None):
    """
    Check if the payload contains all required keys, only allowed keys (if specified), 
    and if provided values match expected types.
    """
    if not data:
        return False, "Error: Payload cannot be empty"
    
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        return False, f"Error: Key(s) {', '.join(missing_keys)} required"
    
    if allowed_keys is not None:
        invalid_keys = [key for key in data if key not in allowed_keys]
        if invalid_keys:
            return False, f"Error: Key(s) {', '.join(invalid_keys)} not accepted in this response"
    
    if key_types is not None:
        for key, expected_type in key_types.items():
            if key in data and not isinstance(data[key], expected_type):
                type_name = expected_type.__name__
                return False, f"Error: Key {key} must be of type {type_name}"
    
    return True, ""

def generate_temp_token(user_id):
    """
    Generate a temporary JWT token for OTP verification.
    """
    payload = {
        'user_id': user_id,
        'exp': int(time.time()) + 300,  # 5 minutes expiration
        'iat': int(time.time()),
        'type': 'temp'
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)