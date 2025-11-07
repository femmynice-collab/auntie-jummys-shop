import os
from decimal import Decimal
from django.db import transaction
from django.utils.text import slugify
from .models import Category, Product

try:
    from square.client import Client
except Exception:
    Client = None

def _client():
    if not Client:
        raise RuntimeError("Square SDK not installed. Run: pip install squareup")
    token = os.getenv("SQUARE_ACCESS_TOKEN","")
    env = os.getenv("SQUARE_ENV","sandbox").lower()
    if not token:
        raise RuntimeError("Missing SQUARE_ACCESS_TOKEN")
    return Client(access_token=token, environment="production" if env=="production" else "sandbox")

def fetch_inventory_counts():
    client = _client()
    try:
        res = client.inventory.batch_retrieve_counts(body={"location_ids": []})
        if res.is_error():
            return {}
        counts = {}
        for c in res.body.get("counts", []):
            oid = c.get("catalog_object_id")
            qty = c.get("quantity")
            if oid and qty is not None:
                try:
                    counts[oid] = int(float(qty))
                except Exception:
                    pass
        return counts
    except Exception:
        return {}

@transaction.atomic
def pull_catalog():
    client = _client()
    cursor = None
    items = {}
    variations = []
    created = updated = 0

    while True:
        res = client.catalog.list_catalog(cursor=cursor, types="ITEM,ITEM_VARIATION")
        if res.is_error():
            raise RuntimeError(str(res.errors))
        result = res.body
        for obj in result.get("objects", []):
            if obj["type"] == "ITEM":
                items[obj["id"]] = obj
            elif obj["type"] == "ITEM_VARIATION":
                variations.append(obj)
        cursor = result.get("cursor")
        if not cursor:
            break

    inv_counts = fetch_inventory_counts()

    for var in variations:
        vdata = var.get("item_variation_data", {})
        item_id = vdata.get("item_id")
        item = items.get(item_id, {})
        name = (item.get("item_data", {}).get("name") or "Square Item").strip()
        vname = vdata.get("name") or ""
        full_name = f"{name} {vname}".strip()
        price = Decimal("0.00")
        pm = vdata.get("price_money")
        if pm and pm.get("amount") is not None:
            price = Decimal(pm["amount"]) / Decimal(100)

        cat_name = item.get("item_data", {}).get("category_id") or "Candy & Snacks"
        category, _ = Category.objects.get_or_create(name=cat_name, defaults={"slug": slugify(cat_name)})
        slug = slugify(full_name)[:200]

        prod, created_flag = Product.objects.get_or_create(slug=slug, defaults={
            "name": full_name,
            "category": category,
            "price": price,
            "stock": 50,
            "active": True,
            "square_variation_id": var.get("id",""),
        })
        # Update stock from inventory if we have a count keyed by this variation id
        var_id = var.get('id')
        if var_id in inv_counts:
            prod.stock = max(0, int(inv_counts[var_id]))
        if not created_flag:
            changed = False
            if prod.name != full_name:
                prod.name = full_name; changed = True
            if prod.category_id != category.id:
                prod.category = category; changed = True
            if price > 0 and prod.price != price:
                prod.price = price; changed = True
            if prod.square_variation_id != var_id:
                prod.square_variation_id = var_id; changed = True
            if changed:
                prod.save()
                updated += 1
            else:
                prod.save()
        else:
            prod.save()
            created += 1

    return created, updated

def push_inventory_deduction(items, reason="SALE"):  # items: list of (square_variation_id, quantity)
    client = _client()
    changes = []
    for var_id, qty in items:
        if not var_id or qty <= 0:
            continue
        changes.append({
            "type": "ADJUSTMENT",
            "adjustment": {
                "catalog_object_id": var_id,
                "from_state": "IN_STOCK",
                "to_state": "SOLD",
                "location_id": os.getenv("SQUARE_LOCATION_ID",""),
                "quantity": str(int(qty)),
                "reason": reason
            }
        })
    if not changes:
        return {"skipped": True}
    body = {"idempotency_key": "inv-adjust-" + os.urandom(6).hex(), "changes": changes}
    res = client.inventory.batch_change_inventory(body)
    if res.is_error():
        raise RuntimeError(str(res.errors))
    return res.body
