from celery import shared_task
from image_processing_system.celery import app
from django.conf import settings
from .models import Product, ProcessingRequest
from PIL import Image
import requests
from io import BytesIO
import os
import csv
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@shared_task(name='core.tasks.process_images', ignore_result=False)
# @app.task(ignore_result=False) 
def process_images(file_path, request_id):
    logger.info(f"Starting image processing for file: {file_path} with request ID: {request_id}")
   
    output_dir = os.path.join(settings.BASE_DIR, 'output_images')
   
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            logger.info(f"row: {row}") 
            product_name = row['Product Name']
            input_urls = row['Input Image Urls'].split(',')
            # print(product_name, "product name in task")
            # print(input_urls, "input urls in task")
            logger.info(f"Product Name: {product_name}")
            logger.info(f"Input URLs: {input_urls}")
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
                    print("hi")
                    img.save(output_path, quality=50)

                    base_url = url.rsplit('/', 1)[0]
                    output_url = f"{base_url}/{output_file_name}"
                    output_urls.append(output_url)
                except IOError as e:
                    print(f"Error opening image from URL {url.strip()}: {e}")
            print(output_urls, "output url in task")
            # Update the database with the output URLs
            # with transaction.atomic():
            product = Product(
                    product_name=product_name,
                    input_urls=','.join(input_urls),
                    output_urls=','.join(output_urls),
                    request_id=request_id,
                    status='completed'
                )
            product.save()
                
            logger.info(f"Product saved: {product}")
            # print(product, "in product task")

    # print(Product.objects.all(), "in task")
    processing_request = ProcessingRequest.objects.get(request_id=request_id)
    processing_request.status = 'completed'
    processing_request.save()
