import json, os, re, base64, hmac, hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from .models import Order
from .square_sync import push_inventory_deduction
from .emails import send_payment_confirmed

def verify_square_signature(request):
    key = os.getenv("SQUARE_WEBHOOK_SIGNATURE_KEY","").encode("utf-8")
    if not key:
        return True  # dev mode
    body = request.body
    mac = hmac.new(key, body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    got = request.headers.get("x-square-hmacsha256-signature") or request.META.get("HTTP_X_SQUARE_HMACSHA256_SIGNATURE")
    return hmac.compare_digest(expected, (got or ""))

@csrf_exempt
def square_payment_webhook(request):
    if request.method != "POST":
        return JsonResponse({"ok": True})
    if not verify_square_signature(request):
        return HttpResponseForbidden("Invalid signature")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"status":"ignored","reason":"invalid json"}, status=400)

    # attempt to find Order # in note/description fields
    payment = data.get("data", {}).get("object", {}).get("payment") or data.get("payment") or {}
    fields = []
    for k in ("note","statement_description","order_id","id"):
        v = payment.get(k)
        if isinstance(v, str): fields.append(v)

    order_id = None
    pat = re.compile(r"[# ](\d{1,7})")
    for t in fields:
        m = pat.search(t)
        if m:
            order_id = int(m.group(1)); break
    if not order_id:
        m = re.search(r"Order\s*#?(\d{1,7})", request.body.decode("utf-8"), re.I)
        if m: order_id = int(m.group(1))

    if not order_id:
        return JsonResponse({"status":"ignored","reason":"no order id text"}, status=200)

    try:
        order = Order.objects.get(id=order_id)
        order.paid = True
        order.save(update_fields=["paid"])
        # email
        try: send_payment_confirmed(order)
        except Exception: pass
        # inventory deduction
        try:
            items = [(i.product.square_variation_id, i.quantity) for i in order.items.all()]
            push_inventory_deduction(items)
        except Exception: pass
        # increment sales_count
        for it in order.items.all():
            p = it.product
            p.sales_count = (p.sales_count or 0) + it.quantity
            p.save(update_fields=['sales_count'])
        return JsonResponse({"updated": order_id})
    except Order.DoesNotExist:
        return JsonResponse({"status":"ignored","reason":"unknown order"}, status=200)
