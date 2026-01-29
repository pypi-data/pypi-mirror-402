from django.contrib import admin
from django_polls.models import Product

admin.site.register(Product)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock_count')