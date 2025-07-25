import firebase_admin
from firebase_admin import credentials

from app.config import SERVICE_ACCOUNT_KEY_PATH


def initialize_firebase():

    if not SERVICE_ACCOUNT_KEY_PATH:
        raise ValueError("SERVICE_ACCESS_KEY_PATH environment variable is not set.")

    # Инициализация Firebase Admin SDK
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
