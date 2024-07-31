# myapp/middleware.py

import json
import jwt  # Ensure you have PyJWT installed
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings
from .models import APILog

class APILogMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # List of endpoints to be logged
        included_endpoints = [
            '/api/login/',
            '/api/flights/',
            '/api/flights/list/',
            '/flights/'
        ]

        # Debug: Print the request method and path
        print(f"Request Method: {request.method}")
        print(f"Request Path: {request.path}")

        # Skip logging for GET requests
        if request.method == 'GET':
            print("Skipping GET request logging")
            return None

        # Check if the request path is in the included_endpoints list
        if not any(request.path.startswith(endpoint) for endpoint in included_endpoints):
            print("Request path not included in endpoints list")
            return None  # Skip logging for excluded endpoints

        # Initialize parameters variable
        parameters = {}
        access_token = None
        username = None

        # Extract username or access token from POST request body if available
        if request.method == 'POST':
            if request.content_type == 'application/json':
                try:
                    request_data = json.loads(request.body)
                    access_token = request_data.get('access', None)
                    username = request_data.get('username', None)
                    parameters = {k: v for k, v in request_data.items() if k != 'access'}
                except json.JSONDecodeError:
                    access_token = None
                    username = None
                    parameters = {}
            else:
                access_token = request.POST.get('access', None)
                username = request.POST.get('username', None)
                parameters = {k: v for k, v in request.POST.items() if k != 'access'}

        # If access token is not found in POST, try headers (for other cases)
        if not access_token:
            access_token = request.headers.get('Authorization', None)
            if access_token and access_token.startswith('Bearer '):
                access_token = access_token[7:]

        # Determine user based on provided username or decoded token
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None
        elif access_token:
            user_id = self.decode_token(access_token)
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    user = None

        # Collect request parameters based on the HTTP method
        if request.method == 'POST':
            if request.content_type == 'application/json':
                try:
                    request_data = json.loads(request.body)
                    parameters = {k: v for k, v in request_data.items() if k != 'access'}
                except json.JSONDecodeError:
                    parameters = {}
            else:
                parameters = {k: v for k, v in request.POST.items() if k != 'access'}

        # Log the API call
        APILog.objects.create(
            user=user if user and not isinstance(user, AnonymousUser) else None,
            method=request.method,
            endpoint=request.path,
            parameters=str(parameters),
            timestamp=timezone.now()
        )
        return None

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print(f"Decoded payload: {payload}")  # Debug: Print the decoded token payload
            user_id = payload.get('user_id')  # Adjust this if your token uses a different key
            print(f"Extracted user_id: {user_id}")  # Debug: Print the extracted user_id
            return user_id
        except jwt.ExpiredSignatureError:
            print("Token has expired")  # Debug: Log expiration error
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")  # Debug: Log invalid token error
            return None
