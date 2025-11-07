from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
import os
from .models import Category, Product, Order, OrderItem, DeliveryZone, DeliveryWindow, PromoCode, PickupWindow, DeliveryRate
from .forms import CheckoutForm
from .square_gate import create_payment_link
from .emails import send_order_received
from .fees import compute_tiered_fee
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta, time

def _pickup_slots(now_local):
    # Generate 30-min slots for today and tomorrow using DeliveryWindow hours
    slots = []  # list of (label, value-iso)
    for day_offset in (0,1):
        day = now_local.date() + timedelta(days=day_offset)
        weekday = (now_local + timedelta(days=day_offset)).weekday()
        windows = PickupWindow.objects.filter(weekday=weekday).order_by('start')
        for w in windows:
            start_dt = timezone.make_aware(datetime.combine(day, w.start))
            end_dt = timezone.make_aware(datetime.combine(day, w.end))
            cur = start_dt
            while cur <= end_dt - timedelta(minutes=30):
                if day_offset == 0 and cur <= now_local:  # don't allow past slots
                    cur += timedelta(minutes=30); continue
                label = cur.strftime('%a %b %d, %I:%M %p')
                slots.append((label, cur.isoformat()))
                cur += timedelta(minutes=30)
    return slots

def home(request):
    categories = Category.objects.all()
    products = Product.objects.filter(active=True)[:24]
    featured = Product.objects.filter(active=True, featured=True)[:12]
    bestsellers = Product.objects.filter(active=True).order_by('-sales_count')[:12]
    return render(request, 'shop/home.html', {
        'categories': categories, 'products': products,
        'featured': featured, 'bestsellers': bestsellers,
        'promos': PromoCode.objects.filter(active=True).order_by('-starts')[:6],
        'near_zip': request.session.get('last_zip'),
        'DOORDASH_URL': os.getenv('DOORDASH_URL')
    })

def category(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    products = cat.products.filter(active=True)
    return render(request, 'shop/category.html', {'category': cat, 'products': products})

def product(request, slug):
    p = get_object_or_404(Product, slug=slug, active=True)
    return render(request, 'shop/product.html', {'product': p})

def _get_cart(session):
    return session.setdefault('cart', {})

def cart_view(request):
    cart = _get_cart(request.session)
    product_ids = [int(pid) for pid in cart.keys()]
    items = []; total = Decimal('0.00')
    if product_ids:
        for p in Product.objects.filter(id__in=product_ids):
            qty = cart.get(str(p.id), 0)
            line = {'product': p, 'quantity': qty, 'subtotal': p.price * qty}
            items.append(line); total += line['subtotal']
    return render(request, 'shop/cart.html', {'items': items, 'total': total})

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, active=True)
    cart = _get_cart(request.session)
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session.modified = True
    messages.success(request, f"Added {product.name} to cart.")
    return redirect('cart')

def cart_remove(request, product_id):
    cart = _get_cart(request.session)
    cart.pop(str(product_id), None)
    request.session.modified = True
    messages.info(request, "Item removed from cart.")
    return redirect('cart')

def checkout(request):
    cart = _get_cart(request.session)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('home')
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # apply promo
            promo_obj = None
            promo_code = form.cleaned_data.get('promo_code','').strip().upper()
            if promo_code:
                now = timezone.now()
                try:
                    pc = PromoCode.objects.get(code__iexact=promo_code, active=True)
                    if (pc.starts and now < pc.starts) or (pc.ends and now > pc.ends):
                        messages.error(request, 'Promo code is not active.'); return redirect('cart')
                    if pc.usage_limit and pc.usage_count >= pc.usage_limit:
                        messages.error(request, 'Promo code has reached its limit.'); return redirect('cart')
                    promo_obj = pc
                except PromoCode.DoesNotExist:
                    messages.error(request, 'Invalid promo code.'); return redirect('cart')

            # Delivery window/zone check (only if delivery)
            fulfillment = form.cleaned_data.get('fulfillment_method','delivery')
            if fulfillment == 'delivery':
                now = timezone.localtime()
                weekday = now.weekday()
                if not DeliveryZone.objects.filter(postal_code=form.cleaned_data['zip_code']).exists():
                    messages.error(request, 'Sorry, your ZIP code is outside our delivery area.')
                    return redirect('cart')
                allowed = False
                for w in DeliveryWindow.objects.filter(weekday=weekday):
                    start_dt = timezone.make_aware(datetime.combine(now.date(), w.start))
                    end_dt = timezone.make_aware(datetime.combine(now.date(), w.end))
                    if start_dt <= now <= end_dt: allowed = True; break
                if not allowed:
                    messages.error(request, 'We are currently outside our delivery window. Please try again during posted hours.')
                    return redirect('cart')
            now = timezone.localtime()
            weekday = now.weekday()
            if not DeliveryZone.objects.filter(postal_code=form.cleaned_data['zip_code']).exists():
                messages.error(request, 'Sorry, your ZIP code is outside our delivery area.')
                return redirect('cart')
            allowed = False
            for w in DeliveryWindow.objects.filter(weekday=weekday):
                start_dt = timezone.make_aware(datetime.combine(now.date(), w.start))
                end_dt = timezone.make_aware(datetime.combine(now.date(), w.end))
                if start_dt <= now <= end_dt: allowed = True; break
            if not allowed:
                messages.error(request, 'We are currently outside our delivery window. Please try again during posted hours.')
                return redirect('cart')

            order = Order.objects.create(
                customer_name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                zip_code=form.cleaned_data['zip_code'],
                fulfillment_method=fulfillment,
                pickup_note=form.cleaned_data.get('pickup_note',''),
                paid=False
            )
            product_ids = [int(pid) for pid in cart.keys()]
            for p in Product.objects.filter(id__in=product_ids):
                qty = cart.get(str(p.id), 0)
                OrderItem.objects.create(order=order, product=p, quantity=qty, price=p.price)
                p.stock = max(0, p.stock - qty); p.save()

            # compute discount
            discount_amount = Decimal('0.00')
            if promo_obj:
                subtotal = Decimal(order.total)
                if promo_obj.discount_type == PromoCode.PERCENT:
                    discount_amount = (subtotal * (Decimal(promo_obj.value)/Decimal(100))).quantize(Decimal('0.01'))
                else:
                    discount_amount = Decimal(promo_obj.value).quantize(Decimal('0.01'))
                if discount_amount > subtotal: discount_amount = subtotal
                order.promo_code = promo_obj.code
                order.discount_amount = discount_amount
                order.save(update_fields=['promo_code','discount_amount'])
                promo_obj.usage_count = (promo_obj.usage_count or 0) + 1
                promo_obj.save(update_fields=['usage_count'])
# delivery fee (by ZIP) if delivery
delivery_fee = Decimal('0.00')
if fulfillment == 'delivery':
    rate = DeliveryRate.objects.filter(postal_code=form.cleaned_data['zip_code']).first()
    if rate:
        delivery_fee = Decimal(rate.fee).quantize(Decimal('0.01'))
order.delivery_fee = delivery_fee
order.save(update_fields=['delivery_fee'])
return redirect('thanks', order_id=order.id
# ---- end payment block ----
else:
    form = CheckoutForm()
    form.fields['pickup_slot'].choices = _pickup_slots(timezone.localtime())
    return render(request, 'shop/checkout.html', {'form': form})

    

def thanks(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/thanks.html', {'order': order})

def search(request):
    q = request.GET.get('q','').strip()
    products = []
    if q:
        products = Product.objects.filter(name__icontains=q, active=True)
    return render(request, 'shop/search.html', {'query': q, 'products': products})


from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
import csv

@staff_member_required
def staff_orders(request):
    qs = Order.objects.order_by('-created')[:200]
    return render(request, 'staff/orders.html', {'orders': qs})

@staff_member_required
def staff_print(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'staff/print.html', {'order': order})

@staff_member_required
def staff_export_csv(request):
    qs = Order.objects.order_by('-created')[:500]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    w = csv.writer(response)
    w.writerow(['id','created','name','email','address','city','state','zip','paid','total','promo','discount','delivery_fee','fulfillment','pickup_at','pickup_note'])
    for o in qs:
        w.writerow([o.id, o.created, o.customer_name, o.email, o.address, o.city, o.state, o.zip_code, o.paid, o.total, o.promo_code, o.discount_amount, o.delivery_fee, o.fulfillment_method, o.pickup_at, o.pickup_note])
    return response


from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from django.http import HttpResponse

@staff_member_required
def staff_labels_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    LABEL_W = 54 * mm
    LABEL_H = 17 * mm
    MARGIN_X = 2 * mm
    MARGIN_Y = 1 * mm

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="labels_order_{order_id}.pdf"'
    from reportlab.pdfgen import canvas as rcanvas
    c = rcanvas.Canvas(response, pagesize=(LABEL_W, LABEL_H))

    for it in order.items.all():
        name = it.product.name[:32]
        sku = (it.product.sku or "")[:20]
        upc = (it.product.upc or "")[:20]
        allergens = (it.product.allergens or "")[:40]

        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 9, name)
        c.setFont("Helvetica", 7)
        c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 18, f"SKU: {sku}  UPC: {upc}")
        if allergens:
            c.setFont("Helvetica-Oblique", 6)
            c.drawString(MARGIN_X, MARGIN_Y + 3, f"Allergens: {allergens}")
        for _ in range(max(1, it.quantity - 1)):
            c.showPage()
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 9, name)
            c.setFont("Helvetica", 7)
            c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 18, f"SKU: {sku}  UPC: {upc}")
            if allergens:
                c.setFont("Helvetica-Oblique", 6)
                c.drawString(MARGIN_X, MARGIN_Y + 3, f"Allergens: {allergens}")
        c.showPage()
    c.save()
    return response
