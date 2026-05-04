# sales/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order, OrderItem
from .models import Product
# Form for adding a product to an order (used in add_item view)
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is None or qty < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return qty

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        if product and product.stock == 0:
            raise forms.ValidationError("This product is out of stock.")
        return cleaned

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        # These are the blank boxes we want the cashier to fill out
        fields = ['cashier', 'status', 'notes'] 
        
        # We add some CSS classes so it looks pretty on the HTML page 💅
        widgets = {
            'cashier': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your name...'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Any special requests?'}),
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'you@example.com'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Choose a username'})
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirm your password'})


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'price', 'stock', 'barcode', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Product name'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input'}),
            'barcode': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional barcode'}),
        }