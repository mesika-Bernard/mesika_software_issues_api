from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
import jwt
import time
import json
from issue_tracker_api import settings
from ..utils import format_response, validate_request_payload, generate_tokens, require_token, blacklist_token, generate_otp, generate_temp_token

User = get_user_model()

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def login(request):
    """Authenticate user and return a temporary token for OTP verification."""
    if request.method != 'POST':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        data = json.loads(request.body)
        # Check required keys and types
        required_keys = ['username', 'password']
        allowed_keys = {'username', 'password'}
        key_types = {'username': str, 'password': str}
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(
                message=error_message,
                data=[],
                http_status=400
            )

        # Authenticate user
        username = data['username']
        password = data['password']
        user = authenticate(request, username=username, password=password)
        if user is None:
            return format_response(
                message="Error : Invalid username or password",
                data=[],
                http_status=401
            )

        # Generate OTP and temporary token
        otp = generate_otp()
        temp_token = generate_temp_token(user.id)
        
        # Store OTP in cache with temp_token as key, expires in 5 minutes
        cache.set(temp_token, {'user_id': user.id, 'otp': otp}, timeout=300)
        
        print('Login OTP', otp)        
        return format_response(
            message="OTP generated",
            data={'temp_token': temp_token},
            http_status=200
        )
    except json.JSONDecodeError:
        return format_response(
            message="Error : Invalid JSON",
            data=[],
            http_status=400
        )

@csrf_exempt
def verify_otp(request):
    """Verify OTP and return access and refresh tokens."""
    if request.method != 'POST':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        data = json.loads(request.body)
        required_keys = ['temp_token', 'otp']
        allowed_keys = {'temp_token', 'otp'}
        key_types = {'temp_token': str, 'otp': str}
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(
                message=error_message,
                data=[],
                http_status=400
            )

        temp_token = data['temp_token']
        stored_data = cache.get(temp_token)

        if not stored_data or stored_data.get('otp') != data['otp']:
            return format_response(
                message="Error : Invalid or expired OTP",
                data=[],
                http_status=401
            )

        user_id = stored_data['user_id']
        user = User.objects.get(id=user_id)
        tokens = generate_tokens(user)

        # Clean up: Remove the temp token entry after successful verification
        cache.delete(temp_token)

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'gender': user.gender,
            'phone_number': user.phone_number,
            'is_staff': user.is_staff,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'is_active': True
        }
        return format_response(
            message="Login successful",
            data=user_data,
            http_status=200
        )
    except json.JSONDecodeError:
        return format_response(
            message="Error : Invalid JSON",
            data=[],
            http_status=400
        )
    except User.DoesNotExist:
        return format_response(
            message="Error : User not found",
            data=[],
            http_status=404
        )

@csrf_exempt
def refresh(request):
    """Refresh an access token using a valid refresh token and blacklist the old access token."""
    if request.method != 'POST':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        data = json.loads(request.body)

        # Validate request payload
        required_keys = ['refresh_token']
        allowed_keys = {'refresh_token'}
        key_types = {'refresh_token': str}
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)

        if not is_valid:
            return format_response(
                message=error_message,
                data=[],
                http_status=400
            )

        refresh_token = data['refresh_token']

        # Decode and validate refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get('type') != 'refresh':
                return format_response(
                    message="Error : Token is not a refresh token",
                    data=[],
                    http_status=401
                )

            user_id = payload.get('user_id')
            user = User.objects.get(id=user_id)

        except jwt.ExpiredSignatureError:
            return format_response(
                message="Error : Refresh token has expired",
                data=[],
                http_status=401
            )
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return format_response(
                message="Error : Invalid refresh token",
                data=[],
                http_status=401
            )

        # Require and validate Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return format_response(
                message="Error : Missing or malformed Authorization header",
                data=[],
                http_status=400
            )

        access_token = auth_header[len('Bearer '):].strip()
        blacklist_token(access_token)

        # Create new access token
        now = int(time.time())
        access_payload = {
            'user_id': user.id,
            'exp': now + settings.JWT_ACCESS_TOKEN_LIFETIME,
            'iat': now,
            'type': 'access'
        }
        new_access_token = jwt.encode(
            access_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        return format_response(
            message="Token refreshed successfully",
            data={'access_token': new_access_token},
            http_status=200
        )

    except json.JSONDecodeError:
        return format_response(
            message="Error : Invalid JSON",
            data=[],
            http_status=400
        )

@csrf_exempt
@require_token
def logout(request):
    """Invalidate access and refresh tokens for logout."""
    if request.method != 'POST':
        return format_response(
            message="Error : Method not allowed",
            data=[],
            http_status=405
        )

    try:
        data = json.loads(request.body)
        required_keys = ['refresh_token']
        allowed_keys = {'refresh_token'}
        key_types = {'refresh_token': str}
        is_valid, error_message = validate_request_payload(data, required_keys, allowed_keys, key_types)
        if not is_valid:
            return format_response(
                message=error_message,
                data=[],
                http_status=400
            )

        refresh_token = data['refresh_token']
        auth_header = request.headers.get('Authorization')
        access_token = auth_header[len('Bearer '):].strip()

        # Validate refresh token
        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if payload['type'] != 'refresh':
                return format_response(
                    message="Error : Token is not a refresh token",
                    data=[],
                    http_status=401
                )
            if payload['user_id'] != request.user.id:
                return format_response(
                    message="Error : Refresh token does not match user",
                    data=[],
                    http_status=401
                )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return format_response(
                message="Error : Invalid or expired refresh token",
                data=[],
                http_status=401
            )

        # Blacklist both tokens
        blacklist_token(access_token)
        blacklist_token(refresh_token)
        return format_response(
            message="Logout successful",
            data=[],
            http_status=200
        )
    except json.JSONDecodeError:
        return format_response(
            message="Error : Invalid JSON",
            data=[],
            http_status=400
        )