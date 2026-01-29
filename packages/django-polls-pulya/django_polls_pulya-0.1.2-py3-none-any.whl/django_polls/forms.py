from django import forms
from django_polls.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock_count']

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError("Price cannot be negative")
        return price

    def stock_count(self):
        stock_count = self.cleaned_data['stock_count']
        if stock_count < 0:
            raise forms.ValidationError("Stock count cannot be negative")
        return stock_count