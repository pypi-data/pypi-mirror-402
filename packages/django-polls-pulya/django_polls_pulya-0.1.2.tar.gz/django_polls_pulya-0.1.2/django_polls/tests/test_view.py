from django.shortcuts import reverse
from django.test import TestCase, SimpleTestCase
from django_polls.models import Product

class IndexTestCase(SimpleTestCase):

    def test_index_template(self):
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'index.html')

    def test_index_words(self):
        response = self.client.get('/')
        self.assertContains(response, 'Welcome to our Store', status_code=200)

class TestProductsPage(TestCase):
    def setUp(self):
        Product.objects.create(name='Laptop', price=1000, stock_count=5)
        Product.objects.create(name='Mouse', price=800, stock_count=14)

    def test_products_uses_correct_template(self):
        response = self.client.get(reverse('products'))
        self.assertTemplateUsed(response, 'products.html')

    def test_products_context(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(len(response.context['products']), 2)
        self.assertContains(response, "Laptop", status_code=200)
        self.assertContains(response, "Mouse", status_code=200)
        self.assertNotContains(response, "No products available")

    def test_products_view_no_products(self):
        Product.objects.all().delete()
        response = self.client.get(reverse('products'))
        self.assertContains(response, "No products available")
        self.assertEqual(len(response.context['products']), 0)