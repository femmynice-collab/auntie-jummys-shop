from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse('category', args=[self.slug])

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sku = models.CharField(max_length=64, blank=True, default='')
    upc = models.CharField(max_length=64, blank=True, default='')
    allergens = models.TextField(blank=True, default='')
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    sales_count = models.PositiveIntegerField(default=0)
    square_variation_id = models.CharField(max_length=64, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    class Meta: ordering = ['name']
    def __str__(self): return self.name
    def get_absolute_url(self): return reverse('product', args=[self.slug])

class Order(models.Model):
    FULFILLMENT = (('delivery','Delivery'),('pickup','Local Pickup'))
    customer_name = models.CharField(max_length=120)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    promo_code = models.CharField(max_length=40, blank=True, default='')
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fulfillment_method = models.CharField(max_length=12, choices=FULFILLMENT, default='delivery')
    pickup_note = models.CharField(max_length=140, blank=True, default='')
    pickup_at = models.DateTimeField(blank=True, null=True)
    class Meta: ordering = ['-created']
    def __str__(self): return f"Order #{self.pk}"
    @property
    def total(self): return sum(item.total for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sku = models.CharField(max_length=64, blank=True, default='')
    upc = models.CharField(max_length=64, blank=True, default='')
    allergens = models.TextField(blank=True, default='')
    @property
    def total(self): return self.quantity * self.price
    def __str__(self): return f"{self.product} x{self.quantity}"

class PromoCode(models.Model):
    PERCENT='percent'; AMOUNT='amount'
    TYPES=[(PERCENT,'Percent'), (AMOUNT,'Amount')]
    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=10, choices=TYPES, default=PERCENT)
    value = models.DecimalField(max_digits=7, decimal_places=2)
    active = models.BooleanField(default=True)
    starts = models.DateTimeField(blank=True, null=True)
    ends = models.DateTimeField(blank=True, null=True)
    usage_limit = models.PositiveIntegerField(blank=True, null=True)
    usage_count = models.PositiveIntegerField(default=0)
    def __str__(self): return self.code

class DeliveryZone(models.Model):
    postal_code = models.CharField(max_length=20, unique=True)
    def __str__(self): return self.postal_code

class DeliveryWindow(models.Model):
    weekday = models.PositiveSmallIntegerField(help_text="0=Monday … 6=Sunday")
    start = models.TimeField()
    end = models.TimeField()
    def __str__(self): return f"{self.weekday} {self.start}-{self.end}"


class PickupWindow(models.Model):
    weekday = models.PositiveSmallIntegerField(help_text="0=Monday … 6=Sunday")
    start = models.TimeField()
    end = models.TimeField()
    def __str__(self): return f"Pickup {self.weekday} {self.start}-{self.end}"

class DeliveryRate(models.Model):
    postal_code = models.CharField(max_length=20, unique=True)
    fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    def __str__(self): return f"{self.postal_code}: ${self.fee}"
