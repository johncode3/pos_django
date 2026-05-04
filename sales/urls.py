# sales/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Custom registration page
    path('register/',               views.register_view,        name='register'),

    # Product catalogue and detail
    path('products/',               views.product_list,         name='product_list'),
    path('products/add/',           views.add_product,          name='add_product'),
    path('products/<int:pk>/edit/',  views.edit_product,        name='edit_product'),
    path('products/<int:pk>/',      views.product_detail,       name='product_detail'),

    # Orders
    path('orders/',                 views.order_list,           name='order_list'),
    path('orders/new/',             views.create_order,         name='create_order'),
    path('orders/<int:pk>/',        views.order_detail,         name='order_detail'),
    path('orders/<int:pk>/status/', views.change_order_status,  name='change_order_status'),
    path('orders/mine/',             views.my_orders,           name='my_orders'),
    path('orders/<int:pk>/items/',  views.add_item,             name='add_item'),
    path('orders/<int:pk>/cancel/', views.cancel_order,         name='cancel_order'),
]