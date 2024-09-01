from celery import shared_task
from image_processing_system.celery import app
from django.conf import settings
from .models import Product, ProcessingRequest
from PIL import Image
import requests
from io import BytesIO
import os
import csv
import logging

logger = logging.getLogger(__name__)

@shared_task(name='core.tasks.process_images', ignore_result=False) 
def process_images(file_path, request_id):
   
    output_dir = os.path.join(settings.BASE_DIR, 'output_images')
   
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            product_name = row['Product Name']
            input_urls = row['Input Image Urls'].split(',')
            output_urls = []
            for url in input_urls:
                response = requests.get(url.strip(), headers=headers)
                response.raise_for_status() 
                try:
                    img = Image.open(BytesIO(response.content))
                    img = img.convert('RGB')

                    # Compress the image by 50%
                    base_name, ext = os.path.splitext(os.path.basename(url))
                    output_file_name = f"{base_name}-output{ext}"
                    output_path = os.path.join(output_dir, output_file_name)
                    img.save(output_path, quality=50)

                    base_url = url.rsplit('/', 1)[0]
                    output_url = f"{base_url}/{output_file_name}"
                    output_urls.append(output_url)
                except IOError as e:
                    print(f"Error opening image from URL {url.strip()}: {e}")
            webhook_url = settings.WEBHOOK_URL
            payload = {'request_id': request_id, 'status': 'completed'}
            try:
                response = requests.post(webhook_url, json=payload)
                response.raise_for_status()
                logger.info(f"Webhook notification sent: {response.status_code}")
            except requests.RequestException as e:
                logger.error(f"Error sending webhook notification: {e}")

            # Update the database with the output URLs
            product = Product(
                    product_name=product_name,
                    input_urls=','.join(input_urls),
                    output_urls=','.join(output_urls),
                    request_id=request_id,
                    status='completed'
                )
            product.save()
            
    processing_request = ProcessingRequest.objects.get(request_id=request_id)
    processing_request.status = 'completed'
    processing_request.save()
    
