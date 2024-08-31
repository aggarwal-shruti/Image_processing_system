from django.db import models

# Create your models here.

class Product(models.Model):
    product_name = models.CharField(max_length=100)
    input_urls = models.TextField()
    output_urls = models.TextField(null=True, blank=True)
    request_id = models.CharField(max_length=36)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (f"{self.product_name}_{self.request_id}")

class ProcessingRequest(models.Model):
    request_id = models.CharField(max_length=36, unique=True)
    status = models.CharField(max_length=20, default="pending")
    file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.request_id