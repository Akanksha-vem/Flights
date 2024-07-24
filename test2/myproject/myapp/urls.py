"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# myapp/urls.py
from django.urls import path
from .views import register,login_api, access_token, post_flight_details,list_flights

urlpatterns = [
    
    path('register/', register, name='register-page'),
    path('api/login/', login_api, name='login_api'),
    path('api/access-token/', access_token, name='access-token'),
    path('api/flights/', post_flight_details, name='post-flight-details'),
    path('api/flights/list/', list_flights, name='list-flights'),
]

