from urllib import response
from django.shortcuts import render

# Create your views here.
# myapp/views.py
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import OneTimeToken,UserRegistrationForm
from .serializers import UserSerializer, OneTimeTokenSerializer
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render,redirect
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status



def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})

        user = User.objects.create_user(username=username, password=password, first_name=first_name, last_name=last_name)
        user.save()
        return render(request,'register_success.html')
        #return redirect('login_api')

    return render(request, 'register.html')

def login_page(request):
    return render(request, 'login.html')

    
from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Debug: Print the received username and password
    print(f"Username: {username}, Password: {password}")

    user = authenticate(request, username=username, password=password)
    
    # Debug: Print authentication result
    if user is None:
        #print("Authentication failed for username:", username)
        return Response({'message': 'Authentication failed','error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate and return one-time token
    OneTimeToken.objects.filter(user=user).delete()
    token = OneTimeToken.objects.create(user=user)
    print('One time token')
    return Response({'message': 'one time token valid for 5 minutes','token': str(token.token)}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def access_token(request):
    token = request.data.get('token')
    try:
        one_time_token = OneTimeToken.objects.get(token=token)
    except OneTimeToken.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
     # Check if the one time token has expired (valid for 5 minutes)
    if timezone.now() - one_time_token.created_at > timedelta(minutes=5):
        return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)

    user = one_time_token.user
    access_token = AccessToken.for_user(user)  # Generate access token
    one_time_token.delete()  # Token should be used only once
    return Response({
        'message': 'Access token is valid for 2 hours',
        'access': str(access_token),  # Return access token
    })


from .models import Flight
from .serializers import FlightSerializer

# myapp/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Flight
from .serializers import FlightSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

def validate_token(request):
    token = request.data.get('token')
    if not token:
        return None

    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except Exception as e:
        return None

@api_view(['POST'])
def post_flight_details(request):
    user = validate_token(request)
    if not user:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = FlightSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# myapp/views.py
@api_view(['POST'])
def list_flights(request):
    user = validate_token(request)
    if not user:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

    flights = Flight.objects.filter(user=user)
    serializer = FlightSerializer(flights, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
