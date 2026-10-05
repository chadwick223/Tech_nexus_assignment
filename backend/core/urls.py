from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('items/<str:item_id>/', views.cart_item, name='cart_item'),
    path('process/command/', views.process_command, name='process_command'),
]
