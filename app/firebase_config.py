import logging
import os

import firebase_admin
from firebase_admin import credentials

from app.config import SERVICE_ACCOUNT_KEY_PATH

logger = logging.getLogger(__name__)


def initialize_firebase() -> None:
    service_account_path = os.getenv("SERVICE_ACCOUNT_KEY_PATH")

    # В CI/CD или тестовой среде можно пропустить инициализацию
    if not service_account_path:
        logger.warning(
            "SERVICE_ACCOUNT_KEY_PATH not set, skipping Firebase initialization"
        )
        return

    if not os.path.exists(service_account_path):
        raise ValueError(
            f"Service account key file not found at {service_account_path}"
        )

    # Инициализация Firebase Admin SDK
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
