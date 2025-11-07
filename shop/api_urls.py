from django.urls import path
from . import api_views

urlpatterns = [
    path('products/', api_views.product_list),
    path('products/<slug:slug>/', api_views.product_detail),
]
