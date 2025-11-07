# Auntie Jummy’s Candy & Snacks — Django + Square

Production-ready starter: products, categories, cart, checkout via **Square Payment Links**, **Square webhook** (signature verified), **Square catalog & inventory sync**, delivery ZIPs & windows, **order emails**, **featured**, **bestsellers**, **promo codes**, and a clean storefront.

## Quick Start
```bash
cd auntie-jummys-shop
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # fill Square + SMTP
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_delivery
python manage.py runserver
```

## Deploy (Render)
- Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start: `gunicorn auntie_jummys.wsgi:application`
- Set env vars from `.env.example` in Render.

## Features
- **Square Checkout** (Payment Links)
- **Webhooks** (`/webhooks/square/`) with signature verification
- **Catalog sync** (Admin → “Sync from Square”), **Inventory sync** on pull + **deduction** after payment
- **Delivery** ZIP zones and daily windows enforced at checkout
- **Emails**: Order received & Payment confirmed (SMTP)
- **Promo codes**: percent/amount, usage limits, validity windows
- **Bestsellers**: auto-tracks sales; shows a home section
- **Featured**: toggle in Admin
- **DoorDash button**: set `DOORDASH_URL` to show

## Domain & Staff Email
1. Buy `auntiejummys.com` (Squarespace Domains).
2. Host on Render and add Custom Domain (`www` CNAME).
3. Root domain redirect to `https://www.auntiejummys.com`.
4. Google Workspace: add MX, SPF, DKIM, DMARC. Create `orders@auntiejummys.com`.

---
Made with ❤ for Auntie Jummy’s Candy & Snacks.

## Business Hours & ZIPs
- Run `python manage.py seed_delivery` to load expanded ZIPs (West Indy region) and day-specific hours:
  - Mon–Thu 11:00–20:00
  - Fri–Sat 11:00–22:00
  - Sun 12:00–18:00
- Adjust anytime in Admin → Delivery Zones / Delivery Windows.

## Promo Schedules
- Run `python manage.py seed_promos` to create/update:
  - `WELCOME10` (10% off, 90 days, 500 uses)
  - `FREESHIP` ($5.00 off, 30 days, 1000 uses)
  - `MOVIENIGHT` (15% off, 45 days, 300 uses)


## Pickup Windows (separate from Delivery)
- Manage in Admin → Pickup Windows. Slots on checkout are built from these.
- Defaults are seeded via `seed_delivery`.

## Delivery Fees by ZIP
- Managed in Admin → Delivery Rates. Seeded defaults: **$3** for core ZIPs (46112, 46122, 46234, 46168), **$5** for extended ZIPs.
- Applied automatically at checkout and included in the Square payment amount.

## Coupon Badges on Products
- A small "Deal" badge displays on product cards whenever any active promo exists.
- The homepage top banner still lists active promo codes.


## Tiered Delivery Fees (Distance-based)
- Set in `.env`: `STORE_ZIP` and `DELIVERY_FEE_TIERS` (e.g., `5:3,10:5,999:8` means up to 5 miles = $3, 5–10 = $5, 10+ = $8).
- Falls back to Admin → Delivery Rates if a ZIP fee is explicitly set.

## Pickup Instructions
- Configure `STORE_ADDRESS`, `STORE_PHONE`. Emails and Thank You page include a Google Maps link.

## Staff Dashboard
- `/staff/orders` (requires admin/staff login) shows latest orders with print-ready packing slips and **CSV export**.
- Print view at `/staff/orders/print/<order_id>/`.


## Product fields for packing & labels
- **SKU**, **UPC**, and **Allergens** added on products (editable in Admin).

## Free Delivery Threshold
- Set `FREE_DELIVERY_THRESHOLD` (e.g., `35.00`) — delivery fee waives when (subtotal − discount) ≥ threshold.

## Thermal Labels (Brother QL, 17×54mm)
- Generate via CLI: `python manage.py make_labels <order_id> --out labels.pdf`
- Or download as staff: `/staff/orders/labels/<order_id>/`
- Includes Product **Name**, **SKU**, **UPC**, and **Allergens**, one label per item quantity.



## Business Hours (updated)
- Delivery & Pickup windows are now seeded for **every day 8:00 AM – 11:00 PM**.
- Run: `python manage.py seed_delivery` to apply (re-run safe; it only creates missing windows).
