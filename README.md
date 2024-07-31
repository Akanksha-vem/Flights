We created .env file in the root directory where it stores the amadeus API_KEY and amadeus API_secret_Key to reducing the risk of them being exposed if the code is shared.
Add this code in settings.py file
import os
from dotenv import load_dotenv
 
load_dotenv()
 
AMADEUS_API_KEY = os.getenv('AMADEUS_API_KEY')
AMADEUS_API_SECRET = os.getenv('AMADEUS_API_SECRET')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}
