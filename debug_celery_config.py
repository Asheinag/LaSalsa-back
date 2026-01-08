import logging

from app.celery_app import celery_app
from app.logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)
logger.info("Broker: %s", celery_app.conf.broker_url)
logger.info("Result backend: %s", celery_app.conf.result_backend)
