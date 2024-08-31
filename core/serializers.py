from rest_framework import serializers
from .models import Product, ProcessingRequest

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        field = '__all__'

class ProcessingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingRequest
        field = '__all__'