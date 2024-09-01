from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings
from .models import Product, ProcessingRequest
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
import json
from .tasks import process_images
import csv
import uuid
import os
import time

class UploadCSV(APIView):
    def post(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'No file part'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return Response({'error': 'Invalid file type. Only CSV files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        request_id = str(uuid.uuid4())
        file_name = file.name
        processing_request = ProcessingRequest(request_id=request_id, file_name=file_name)
        processing_request.save()

        upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Saving the file
        file_path = os.path.join(settings.BASE_DIR, 'uploads', file_name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        result = process_images.delay(file_path, request_id)
        time.sleep(5)
        output_csv = self.generate_output_csv(request_id)

        return Response({'request_id': request_id}, status=status.HTTP_202_ACCEPTED)


    def generate_output_csv(self, request_id):
            products = Product.objects.filter(request_id=request_id)

            output_dir = os.path.join(settings.BASE_DIR, 'output_csvs')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            output_file_path = os.path.join(output_dir, f'output_{request_id}.csv')
            try:
                with open(output_file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Serial Number', 'Product Name', 'Input Image Urls', 'Output Image Urls'])
                    for index, product in enumerate(products, start=1):
                        writer.writerow([
                            index,
                            product.product_name,
                            product.input_urls,
                            product.output_urls
                        ])
            except Exception as e:
                raise

            return output_file_path   


class CheckStatus(APIView):
   def get(self, request, request_id):
        try:
            processing_request = ProcessingRequest.objects.get(request_id=request_id)
        except ProcessingRequest.DoesNotExist:
            return Response({'error': 'Invalid request ID'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'request_id': processing_request.request_id,
            'status': processing_request.status
        }, status=status.HTTP_200_OK)
   

class WebhookHandlerView(View):

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            status = data.get('status')

            return JsonResponse({'message': 'Webhook received'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

