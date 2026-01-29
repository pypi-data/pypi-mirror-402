from django.test import TestCase
from django_polls.models import Product
from django.db.utils import IntegrityError

class ProductModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product(name='Product Name', price=100.00, stock_count= 10)

    def test_in_stock_property(self):
        self.product.stock_count = 0
        self.assertFalse(self.product.in_stock)

    # def test_negative_price_validation(self):
    #     self.product.price = -1
    #     with self.assertRaises(ValidationError):
    #         self.product.clean()
    #
    # def test_negative_validation(self):
    #     self.product.stock_count = -1
    #     with self.assertRaises(ValidationError):
    #         self.product.clean()

    def test_get_discount_price(self):
        self.assertEqual(self.product.get_discount_price(10), 90)
        self.assertEqual(self.product.get_discount_price(0), 100)
        self.assertEqual(self.product.get_discount_price(50), 50)

    def test_negative_price_constraint(self):
        self.product.price = -1
        with self.assertRaises(IntegrityError):
            self.product.save()

    def test_negative_stock_count_constraint(self):
        self.product.stock_count = -1
        with self.assertRaises(IntegrityError):
            self.product.save()