
# sales/models.py
from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('food',        'Food & Drink'),
        ('electronics', 'Electronics'),
        ('clothing',    'Clothing'),
        ('household',   'Household'),
        ('other',       'Other'),
    ]

    name       = models.CharField(max_length=200)
    category   = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price      = models.DecimalField(max_digits=8, decimal_places=2)   # e.g. 12.99
    stock      = models.PositiveIntegerField(default=0)                # units in stock
    barcode    = models.CharField(max_length=50, unique=True, blank=True)
    is_active  = models.BooleanField(default=True)                     # hide discontinued items
    image      = models.ImageField(upload_to='product_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.name}  —  ${self.price}  (stock: {self.stock})"

    class Meta:
        ordering = ['name']


class Order(models.Model):
    STATUS_CHOICES = [
        ('open',       'Open'),
        ('on_hold',    'On Hold'),
        ('paid',       'Paid'),
        ('refunded',   'Refunded'),
        ('cancelled',  'Cancelled'),
    ]

    cashier    = models.ForeignKey(
                    User,
                    on_delete=models.SET_NULL,   # keep the order if the staff account is deleted
                    null=True,
                    related_name='orders',
                 )

    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)    # set when the order is created
    notes      = models.TextField(blank=True)

    @property
    def total(self):
        """Sum the subtotal, then subtract the discount if they have one! 💸"""
        subtotal = sum(item.subtotal for item in self.items.all())
        # Check if the order has a discount attached to it
        if hasattr(self, 'discount'):
            return subtotal - self.discount.amount
        return subtotal

    def __str__(self):
        return f"Order #{self.pk}  [{self.status.upper()}]  —  ${self.total:.2f}"

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product    = models.ForeignKey(Product, on_delete=models.PROTECT)   # PROTECT prevents deleting a product that has sales
    quantity   = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)    # price at time of sale

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.product.name}  @  ${self.unit_price}"

    # 👇 THE AUTO-STOCK MAGIC (Add this right here!) 👇
    def save(self, *args, **kwargs):
        # 1. Check if this is a BRAND NEW item being added to the order
        # If pk is None, it means it hasn't been saved to the database yet.
        is_new = self.pk is None 
        
        # 2. Save the item normally first (Django's default job)
        super().save(*args, **kwargs)
        
        # 3. If it's a new sale, deduct the stock from the warehouse! 📉
        if is_new:
            self.product.stock -= self.quantity
            self.product.save()

class Discount(models.Model):
    # OneToOne means an order can only have ONE discount applied to it.
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='discount')
    description = models.CharField(max_length=200)   # e.g. "Staff discount"
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.description} (-${self.amount}) on Order #{self.order.pk}"