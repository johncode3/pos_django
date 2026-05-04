# sales/views.py

# 1️⃣ ADDED 'redirect' right here! 👇
from django.shortcuts import render, get_object_or_404, redirect

from .models import Product, Order, OrderItem
from .forms import OrderItemForm, RegisterForm, ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def product_list(request):
    """Show all active products, sorted A–Z. Now with Search Aura! 🔍"""
    query = request.GET.get('q') 
    
    if query:
        products = Product.objects.filter(name__icontains=query, is_active=True).order_by('name')
    else:
        products = Product.objects.filter(is_active=True).order_by('name')
        
    return render(request, 'sales/product_list.html', {'products': products})

@login_required
def product_detail(request, pk):
    """Show details for a single product. Return 404 if not found."""
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'sales/product_detail.html', {'product': product})

@login_required
def order_list(request):
    """Show all orders, most recent first."""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'sales/order_list.html', {'orders': orders})


# 3️⃣ THE NEW IPAD FRONT DESK VIEW 📱 👇

# --- POS Order Creation and Item Addition ---
@login_required
def create_order(request):
    """Create or reuse an open order for this cashier and go to the add-items page."""
    # Reuse an existing open order for the cashier so repeated "new" clicks
    # don't create many empty orders and consume auto-increment ids.
    order = Order.objects.filter(cashier=request.user, status='open').first()
    if not order:
        order = Order.objects.create(
            cashier=request.user,
            status='open',
        )
    return redirect('add_item', pk=order.pk)


@login_required
def add_item(request, pk):
    """
    Let the cashier add line items to an open order, then mark it paid.
    """
    order = get_object_or_404(Order, pk=pk)

    # Prevent adding items if the order is not open
    if order.status != 'open':
        messages.error(request, 'This order is not open and cannot be modified.')
        return redirect('order_detail', pk=order.pk)

    if request.method == 'POST':
        # "Mark as Paid" button
        if 'mark_paid' in request.POST:
            order.status = 'paid'
            order.save()
            return redirect('order_list')

        # Remove an existing line item
        if 'remove_item' in request.POST:
            item_id = request.POST.get('remove_item')
            try:
                item = order.items.get(pk=item_id)
            except OrderItem.DoesNotExist:
                messages.error(request, 'Item not found.')
                return redirect('add_item', pk=order.pk)

            # restore stock
            product = item.product
            product.stock = (product.stock or 0) + item.quantity
            product.save()
            item.delete()
            return redirect('add_item', pk=order.pk)

        # Add a line item
        item_form = OrderItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.order      = order
            item.unit_price = item.product.price 
            item.save()
            messages.success(request, f"✓ Added {item.quantity}× {item.product.name} to order")
            return redirect('add_item', pk=order.pk)
        else:
            # Show validation errors
            for field, errs in item_form.errors.items():
                for error in errs:
                    messages.error(request, f"{error}")
    else:
        item_form = OrderItemForm()

    return render(request, 'sales/add_order.html', {
        'order':     order,
        'item_form': item_form,
        'items':     order.items.select_related('product'),
    })


@login_required
def cancel_order(request, pk):
    """Cancel or delete an order.

    - If the order has no items, delete it (so empty orders don't linger).
    - If it has items, mark it cancelled.
    """
    order = get_object_or_404(Order, pk=pk)

    # Only allow the cashier who created it (or any logged-in staff) to cancel
    if order.cashier != request.user and not request.user.is_staff:
        return redirect('order_list')

    if request.method == 'POST':
        if order.items.exists():
            # Restore stock for each item if this order is not already cancelled.
            if order.status != 'cancelled':
                for item in order.items.select_related('product').all():
                    product = item.product
                    product.stock = (product.stock or 0) + item.quantity
                    product.save()
            order.status = 'cancelled'
            order.save()
        else:
            order.delete()

    return redirect('order_list')


def register_view(request):
    """Create a new POS user account."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'registration/register_form.html', {'form': form})


@login_required
def add_product(request):
    """Create a new product (with optional image)."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'sales/add_product.html', {'form': form})


@login_required
def edit_product(request, pk):
    """Edit an existing product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            # Handle clear image checkbox
            if request.POST.get('clear_image'):
                # delete file from storage if present
                if product.image:
                    try:
                        product.image.delete(save=False)
                    except Exception:
                        pass
                    product.image = None
            form.save()
            product.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'sales/edit_product.html', {'form': form, 'product': product})


@login_required
def order_detail(request, pk):
    """Show a single order with items and allow cancelling from here."""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'sales/order_detail.html', {
        'order': order,
        'items': order.items.select_related('product')
    })


@login_required
def change_order_status(request, pk):
    """Change an order's status (e.g., put on hold or mark as paid)."""
    order = get_object_or_404(Order, pk=pk)

    # Only allow the cashier who created it (or staff) to change status
    if order.cashier != request.user and not request.user.is_staff:
        return redirect('order_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            # Only allow certain transitions
            if new_status == 'cancelled':
                # Use existing cancel logic
                return redirect('cancel_order', pk=order.pk)
            order.status = new_status
            order.save()

    return redirect('order_detail', pk=order.pk)


@login_required
def my_orders(request):
    """Show only orders created by the current user."""
    orders = Order.objects.filter(cashier=request.user).order_by('-created_at')
    return render(request, 'sales/order_list.html', {'orders': orders})