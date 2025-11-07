from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import Category, Product, Order, OrderItem, DeliveryZone, DeliveryWindow, PromoCode, PickupWindow, DeliveryRate
from .square_sync import pull_catalog

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "slug")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name","price","stock","category","active","featured","sku","upc","square_variation_id","sales_count")
    list_filter = ("active","featured","category")
    search_fields = ("name","description","sku","upc")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id","customer_name","email","created","paid","fulfillment_method","promo_code","discount_amount","delivery_fee")
    list_filter = ("paid","created")
    inlines = [OrderItemInline]

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code","discount_type","value","active","usage_count","usage_limit","starts","ends")
    search_fields = ("code",)
    list_filter = ("active","discount_type")

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("postal_code",)
    search_fields = ("postal_code",)

@admin.register(DeliveryWindow)
class DeliveryWindowAdmin(admin.ModelAdmin):
    list_display = ("weekday","start","end")
    list_filter = ("weekday",)

# Admin URL to trigger Square sync
def sync_from_square(request):
    try:
        created, updated = pull_catalog()
        messages.success(request, f"Square sync: {created} created, {updated} updated.")
    except Exception as e:
        messages.error(request, f"Square sync failed: {e}")
    return redirect('/admin/')

def get_urls_with_sync(self):
    urls = super(type(self), self).get_urls()
    return [path('shop/sync-square/', sync_from_square, name='sync-square')] + urls

admin.site.get_urls = get_urls_with_sync.__get__(admin.site, type(admin.site))

# Add link on admin index
from django.contrib.admin.sites import site as default_site
orig_index = default_site.index
def index_with_link(request, extra_context=None):
    extra = extra_context or {}
    extra['square_sync_link'] = '/admin/shop/sync-square/'
    return orig_index(request, extra)
default_site.index = index_with_link


@admin.register(PickupWindow)
class PickupWindowAdmin(admin.ModelAdmin):
    list_display = ("weekday","start","end")
    list_filter = ("weekday",)

@admin.register(DeliveryRate)
class DeliveryRateAdmin(admin.ModelAdmin):
    list_display = ("postal_code","fee")
    search_fields = ("postal_code",)
