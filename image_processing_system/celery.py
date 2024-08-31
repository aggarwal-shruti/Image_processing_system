from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'image_processing_system.settings')

app = Celery('image_processing_system')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['core'])
