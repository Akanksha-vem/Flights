
from django.urls import path


from .views import flight_both_view,flight_date_view,flight_summary_view,flight_place_view
 
urlpatterns = [
     path('both/', flight_both_view, name='flight-both'),
    path('place/', flight_place_view,name='place'),
    path('date/', flight_date_view, name='date'),
     path('flight-summary/', flight_summary_view, name='By date and place')
]

