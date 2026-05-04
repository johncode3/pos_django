# sales/admin.py

from django.contrib import admin
from .models import Product, Order, OrderItem, Discount

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  =['name', 'category', 'price', 'stock', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['name', 'barcode']
    ordering      = ['name']

class OrderItemInline(admin.TabularInline):
    """Show order items directly inside the Order edit page."""
    model  = OrderItem
    extra  = 1    # number of empty rows displayed for adding new items
    fields =['product', 'quantity', 'unit_price']

# 👇 THE NEW DISCOUNT INLINE MAGIC 👇
class DiscountInline(admin.StackedInline):
    """Show the discount field directly inside the Order edit page."""
    model = Discount
    extra = 0     # 0 because not every order gets a discount!

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  =['pk', 'cashier', 'status', 'created_at']
    list_filter   = ['status']
    search_fields = ['cashier', 'notes']
    ordering      = ['-created_at']
    # 👇 Add the DiscountInline right next to OrderItemInline! 👇
    inlines       = [OrderItemInline, DiscountInline]    

# 👇 Optional: Register Discount by itself just in case you want to see a list of all discounts given
@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['order', 'description', 'amount']