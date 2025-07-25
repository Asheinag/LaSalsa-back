from app.celery_app import celery_app

print("Broker:", celery_app.conf.broker_url)
print("Result backend:", celery_app.conf.result_backend)
