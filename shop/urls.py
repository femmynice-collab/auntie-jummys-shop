from django.urls import path
from . import views

urlpatterns = [
    path('staff/orders/labels/<int:order_id>/', views.staff_labels_pdf, name='staff_labels_pdf'),
    path('staff/orders/', views.staff_orders, name='staff_orders'),
    path('staff/orders/print/<int:order_id>/', views.staff_print, name='staff_print'),
    path('staff/orders/export.csv', views.staff_export_csv, name='staff_export_csv'),
    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category, name='category'),
    path('product/<slug:slug>/', views.product, name='product'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('thanks/<int:order_id>/', views.thanks, name='thanks'),
    path('search/', views.search, name='search'),
]
