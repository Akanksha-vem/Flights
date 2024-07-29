import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import FlightSummarySerializer,PlaceDateSerializer,DateSerializer,PlaceSerializer
import logging
from datetime import datetime
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
import pytz  # Import pytz for timezone handling
import certifi
from django.conf import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

AMADEUS_BASE_URL = 'https://test.api.amadeus.com'  # Use production URL for live environment
#getting amadeus token
def get_amadeus_access_token():
    url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': settings.AMADEUS_API_KEY,
        'client_secret': settings.AMADEUS_API_SECRET
    }
    try:
        response = requests.post(url, data=payload, verify=certifi.where())
        response.raise_for_status()
        token = response.json().get('access_token')
        logger.debug(f"Access Token: {token}")
        return token
    except requests.RequestException as e:
        logger.error(f'Error obtaining access token: {str(e)}')
        return None
#get IATA code
def get_iata_code(place, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'{AMADEUS_BASE_URL}/v1/reference-data/locations?keyword={place}&subType=AIRPORT'
    try:
        response = requests.get(url, headers=headers, verify=certifi.where())
        response.raise_for_status()
        location_data = response.json()
        if location_data['data']:
            return location_data['data'][0]['iataCode']
    except requests.RequestException as e:
        logger.error(f"Error fetching IATA code: {str(e)}")
    return None
#Get Place name 
def get_place_name(iata_code, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'{AMADEUS_BASE_URL}/v1/reference-data/locations?keyword={iata_code}&subType=AIRPORT'
    try:
        response = requests.get(url, headers=headers, verify=certifi.where())
        response.raise_for_status()
        location_data = response.json()
        if location_data['data']:
            airport_info = location_data['data'][0]
            city_name = airport_info.get('address', {}).get('cityName', 'Unknown City')
            return city_name
    except requests.RequestException as e:
        logger.error(f"Error fetching place name: {str(e)}")
    return iata_code  # Return IATA code if city name is not found

#FLIGHT SUMMARY 
@api_view(['POST'])
def flight_summary_view(request):
    serializer = FlightSummarySerializer(data=request.data)
    if serializer.is_valid():
        access_token_str = serializer.validated_data['access']
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        access_token = AccessToken(access_token_str)
    except Exception as e:
        logger.error(f'Error validating access token: {str(e)}')
        return Response({'error': 'Invalid or expired access token'}, status=status.HTTP_401_UNAUTHORIZED)

    token_expiration_time = datetime.fromtimestamp(access_token['exp'], tz=pytz.UTC)  # Use pytz.UTC here

    if timezone.now() > token_expiration_time:
        return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)

    amadeus_access_token = get_amadeus_access_token()
    if not amadeus_access_token:
        return Response({'error': 'Failed to obtain Amadeus access token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    headers = {'Authorization': f'Bearer {amadeus_access_token}'}
    iata_codes = ['BOM', 'DEL']
    current_date = datetime.now().strftime('%Y-%m-%d')

    result = {}

    for iata_code in iata_codes:
        incoming_flights_count = 0
        outgoing_flights_count = 0

        for code in iata_codes:
            if code != iata_code:
                # Fetch outgoing flights
                outgoing_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
                outgoing_params = {
                    'originLocationCode': iata_code,
                    'destinationLocationCode': code,
                    'departureDate': current_date,  # Use provided date
                    'adults': 1  # Example: Add other required parameters
                }

                logger.debug(f"Outgoing Flights Request URL: {outgoing_endpoint}")
                logger.debug(f"Outgoing Flights Headers: {headers}")
                logger.debug(f"Outgoing Flights Params: {outgoing_params}")

                outgoing_response = requests.get(outgoing_endpoint, headers=headers, params=outgoing_params)
                logger.debug(f"Outgoing Flights Response Status Code: {outgoing_response.status_code}")
                logger.debug(f"Outgoing Flights Response Content: {outgoing_response.content}")

                if outgoing_response.status_code == 200:
                    outgoing_flight_data = outgoing_response.json()
                    outgoing_flights_count += len(outgoing_flight_data.get('data', []))
                else:
                    logger.error(f"Failed to fetch outgoing flight data: {outgoing_response.json()}")

                # Fetch incoming flights
                incoming_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
                incoming_params = {
                    'destinationLocationCode': iata_code,
                    'originLocationCode': code,
                    'departureDate': current_date,  # Use provided date
                    'adults': 1  # Example: Add other required parameters
                }

                logger.debug(f"Incoming Flights Request URL: {incoming_endpoint}")
                logger.debug(f"Incoming Flights Headers: {headers}")
                logger.debug(f"Incoming Flights Params: {incoming_params}")

                incoming_response = requests.get(incoming_endpoint, headers=headers, params=incoming_params)
                logger.debug(f"Incoming Flights Response Status Code: {incoming_response.status_code}")
                logger.debug(f"Incoming Flights Response Content: {incoming_response.content}")

                if incoming_response.status_code == 200:
                    incoming_flight_data = incoming_response.json()
                    incoming_flights_count += len(incoming_flight_data.get('data', []))
                else:
                    logger.error(f"Failed to fetch incoming flight data: {incoming_response.json()}")

        total_flights_count = incoming_flights_count + outgoing_flights_count
        result[iata_code] = {
            'place': iata_code,
            'incoming_flights': incoming_flights_count,
            'outgoing_flights': outgoing_flights_count,
            'total_flights': total_flights_count
        }

    return Response(result)

#By place 
@api_view(['POST'])
def flight_place_view(request):
    serializer = PlaceSerializer(data=request.data)
    if serializer.is_valid():
        place = serializer.validated_data['place']
        access_token_str = serializer.validated_data.get('access')  # Access token from the payload
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Validate the access token
    try:
        access_token = AccessToken(access_token_str)
    except Exception as e:
        logger.error(f'Error validating access token: {str(e)}')
        return Response({'error': 'Invalid or expired access token'}, status=status.HTTP_401_UNAUTHORIZED)

    token_expiration_time = datetime.fromtimestamp(access_token['exp'], tz=pytz.UTC)  # Use pytz.UTC here

    if timezone.now() > token_expiration_time:
        return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)

    amadeus_access_token = get_amadeus_access_token()
    if not amadeus_access_token:
        return Response({'error': 'Failed to obtain Amadeus access token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    iata_code = get_iata_code(place, amadeus_access_token)
    if not iata_code:
        return Response({'error': 'Invalid place or IATA code not found'}, status=status.HTTP_400_BAD_REQUEST)

    headers = {'Authorization': f'Bearer {amadeus_access_token}'}
    # Fetch outgoing flights
    iata_codes = ['BOM', 'DEL', 'BLR', 'MAA', 'HYD', 'PNQ', 'AMD', 'GOI', 'COK', 'CCU']
    # current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    incoming_flights_count = 0
    outgoing_flights_count = 0

    for code in iata_codes:
        if code != iata_code:
            # Fetch outgoing flights
            outgoing_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
            outgoing_params = {
                'originLocationCode': iata_code,
                'destinationLocationCode': code,
                'departureDate': current_date,  # Example: Add a date or other required parameters
                'adults': 1  # Example: Add other required parameters
            }

            logger.debug(f"Outgoing Flights Request URL: {outgoing_endpoint}")
            logger.debug(f"Outgoing Flights Headers: {headers}")
            logger.debug(f"Outgoing Flights Params: {outgoing_params}")

            outgoing_response = requests.get(outgoing_endpoint, headers=headers, params=outgoing_params)
            logger.debug(f"Outgoing Flights Response Status Code: {outgoing_response.status_code}")
            logger.debug(f"Outgoing Flights Response Content: {outgoing_response.content}")

            if outgoing_response.status_code == 200:
                outgoing_flight_data = outgoing_response.json()
                outgoing_flights_count += len(outgoing_flight_data.get('data', []))
            else:
                logger.error(f"Failed to fetch outgoing flight data: {outgoing_response.json()}")

            # Fetch incoming flights
            incoming_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
            incoming_params = {
                'destinationLocationCode': iata_code,
                'originLocationCode': code,
                'departureDate': current_date,  # Example: Add a date or other required parameters
                'adults': 1  # Example: Add other required parameters
            }

            logger.debug(f"Incoming Flights Request URL: {incoming_endpoint}")
            logger.debug(f"Incoming Flights Headers: {headers}")
            logger.debug(f"Incoming Flights Params: {incoming_params}")

            incoming_response = requests.get(incoming_endpoint, headers=headers, params=incoming_params)
            logger.debug(f"Incoming Flights Response Status Code: {incoming_response.status_code}")
            logger.debug(f"Incoming Flights Response Content: {incoming_response.content}")

            if incoming_response.status_code == 200:
                incoming_flight_data = incoming_response.json()
                incoming_flights_count += len(incoming_flight_data.get('data', []))
            else:
                logger.error(f"Failed to fetch incoming flight data: {incoming_response.json()}")

    total_flights_count = incoming_flights_count + outgoing_flights_count
    return Response({
        'incoming_flights_count': incoming_flights_count,
        'outgoing_flights_count': outgoing_flights_count,
        'total_flights': total_flights_count
    })

    
# by date
@api_view(['POST'])
def flight_date_view(request):
    serializer = DateSerializer(data=request.data)
    if serializer.is_valid():
        flight_date = serializer.validated_data['date']
        access_token_str = serializer.validated_data.get('access')  # Access token from the payload
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Validate the access token
    try:
        access_token = AccessToken(access_token_str)
    except Exception as e:
        logger.error(f'Error validating access token: {str(e)}')
        return Response({'error': 'Invalid or expired access token'}, status=status.HTTP_401_UNAUTHORIZED)

    token_expiration_time = datetime.fromtimestamp(access_token['exp'], tz=pytz.UTC)  # Use pytz.UTC here

    if timezone.now() > token_expiration_time:
        return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)

    amadeus_access_token = get_amadeus_access_token()
    if not amadeus_access_token:
        return Response({'error': 'Failed to obtain Amadeus access token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    headers = {'Authorization': f'Bearer {amadeus_access_token}'}
    iata_codes = ['BOM','DEL', 'BLR']
    

    result = {}

    for iata_code in iata_codes:
        incoming_flights_count = 0
        outgoing_flights_count = 0

        for code in iata_codes:
            if code != iata_code:
                # Fetch outgoing flights
                outgoing_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
                outgoing_params = {
                    'originLocationCode': iata_code,
                    'destinationLocationCode': code,
                    'departureDate': flight_date,  # Use provided date
                    'adults': 1  # Example: Add other required parameters
                }

                logger.debug(f"Outgoing Flights Request URL: {outgoing_endpoint}")
                logger.debug(f"Outgoing Flights Headers: {headers}")
                logger.debug(f"Outgoing Flights Params: {outgoing_params}")

                outgoing_response = requests.get(outgoing_endpoint, headers=headers, params=outgoing_params)
                logger.debug(f"Outgoing Flights Response Status Code: {outgoing_response.status_code}")
                logger.debug(f"Outgoing Flights Response Content: {outgoing_response.content}")

                if outgoing_response.status_code == 200:
                    outgoing_flight_data = outgoing_response.json()
                    outgoing_flights_count += len(outgoing_flight_data.get('data', []))
                else:
                    logger.error(f"Failed to fetch outgoing flight data: {outgoing_response.json()}")

                # Fetch incoming flights
                incoming_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
                incoming_params = {
                    'destinationLocationCode': iata_code,
                    'originLocationCode': code,
                    'departureDate': flight_date,  # Use provided date
                    'adults': 1  # Example: Add other required parameters
                }

                logger.debug(f"Incoming Flights Request URL: {incoming_endpoint}")
                logger.debug(f"Incoming Flights Headers: {headers}")
                logger.debug(f"Incoming Flights Params: {incoming_params}")

                incoming_response = requests.get(incoming_endpoint, headers=headers, params=incoming_params)
                logger.debug(f"Incoming Flights Response Status Code: {incoming_response.status_code}")
                logger.debug(f"Incoming Flights Response Content: {incoming_response.content}")

                if incoming_response.status_code == 200:
                    incoming_flight_data = incoming_response.json()
                    incoming_flights_count += len(incoming_flight_data.get('data', []))
                else:
                    logger.error(f"Failed to fetch incoming flight data: {incoming_response.json()}")

        total_flights_count = incoming_flights_count + outgoing_flights_count
        # Fetch place name dynamically
        city_name = get_place_name(iata_code, amadeus_access_token)
        result[city_name] = {
            'place': city_name,
            'incoming_flights': incoming_flights_count,
            'outgoing_flights': outgoing_flights_count,
            'total_flights': total_flights_count
        }
    return Response(result)

#By BOTH PLACE AND DATE

@api_view(['POST'])
def flight_both_view(request):
    serializer = PlaceDateSerializer(data=request.data)
    if serializer.is_valid():
        place = serializer.validated_data['place']
        date = serializer.validated_data['date']
        access_token_str = serializer.validated_data.get('access')  # Access token from the payload
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Validate the access token
    try:
        access_token = AccessToken(access_token_str)
    except:
        return Response({'error': 'Invalid or expired access token'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token_expiration_time = datetime.fromtimestamp(access_token['exp'], tz=pytz.UTC)

    if timezone.now() > token_expiration_time:
        return Response({'error': 'Token expired'}, status=status.HTTP_401_UNAUTHORIZED)

    # Get Amadeus access token
    amadeus_access_token = get_amadeus_access_token()
    if not amadeus_access_token:
        return Response({'error': 'Failed to obtain Amadeus access token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Get IATA code for the place
    iata_code = get_iata_code(place, amadeus_access_token)
    if not iata_code:
        return Response({'error': 'Invalid place or IATA code not found'}, status=status.HTTP_400_BAD_REQUEST)

    headers = {'Authorization': f'Bearer {amadeus_access_token}'}
    iata_codes = ['BOM', 'DEL', 'BLR']

    incoming_flights_count = 0
    outgoing_flights_count = 0

    for code in iata_codes:
        if code != iata_code:
            # Fetch outgoing flights
            outgoing_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
            outgoing_params = {
                'originLocationCode': iata_code,
                'destinationLocationCode': code,
                'departureDate': date,  # Use the provided date
                'adults': 1  # Example: Add other required parameters
            }

            logger.debug(f"Outgoing Flights Request URL: {outgoing_endpoint}")
            logger.debug(f"Outgoing Flights Headers: {headers}")
            logger.debug(f"Outgoing Flights Params: {outgoing_params}")

            outgoing_response = requests.get(outgoing_endpoint, headers=headers, params=outgoing_params)
            logger.debug(f"Outgoing Flights Response Status Code: {outgoing_response.status_code}")
            logger.debug(f"Outgoing Flights Response Content: {outgoing_response.content}")

            if outgoing_response.status_code == 200:
                outgoing_flight_data = outgoing_response.json()
                outgoing_flights_count += len(outgoing_flight_data.get('data', []))
            else:
                logger.error(f"Failed to fetch outgoing flight data: {outgoing_response.json()}")

            # Fetch incoming flights
            incoming_endpoint = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
            incoming_params = {
                'destinationLocationCode': iata_code,
                'originLocationCode': code,
                'departureDate': date,  # Use the provided date
                'adults': 1  # Example: Add other required parameters
            }

            logger.debug(f"Incoming Flights Request URL: {incoming_endpoint}")
            logger.debug(f"Incoming Flights Headers: {headers}")
            logger.debug(f"Incoming Flights Params: {incoming_params}")

            incoming_response = requests.get(incoming_endpoint, headers=headers, params=incoming_params)
            logger.debug(f"Incoming Flights Response Status Code: {incoming_response.status_code}")
            logger.debug(f"Incoming Flights Response Content: {incoming_response.content}")

            if incoming_response.status_code == 200:
                incoming_flight_data = incoming_response.json()
                incoming_flights_count += len(incoming_flight_data.get('data', []))
            else:
                logger.error(f"Failed to fetch incoming flight data: {incoming_response.json()}")

    total_flights_count = incoming_flights_count + outgoing_flights_count

    return Response({
        'incoming_flights': incoming_flights_count,
        'outgoing_flights': outgoing_flights_count,
        'no_of_flights': total_flights_count
    })

