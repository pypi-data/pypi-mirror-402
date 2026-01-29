from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    pass

class Product(models.Model):
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_count = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock_count__gt=0),
                name='stock_count greater than 0',
            ),models.CheckConstraint(
                condition=models.Q(price__gt=0),
                name='price greater than zero'
            ),
        ]

    def __str__(self):
        return f"{self.name} | {self.price} | {self.stock_count}"

    def get_discount_price(self, discount_percentage):
        return self.price * (1-discount_percentage / 100)

    @property
    def in_stock(self) -> bool:
        return self.stock_count > 0

    # def clean(self):
    #     if self.price < 0:
    #         raise ValidationError('Price cannot be negative')
    #     if self.stock_count < 0:
    #         raise ValidationError('Stock count cannot be negative')