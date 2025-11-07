import os
from decimal import Decimal
try:
    from square.client import Client
except Exception:
    Client = None

def get_client():
    if not Client:
        raise RuntimeError("Square SDK not installed. Run: pip install squareup")
    env = os.getenv("SQUARE_ENV", "sandbox")
    token = os.getenv("SQUARE_ACCESS_TOKEN", "")
    if not token:
        raise RuntimeError("Missing SQUARE_ACCESS_TOKEN")
    return Client(access_token=token, environment="production" if env.lower()=="production" else "sandbox")

def create_payment_link(order_id: int, amount: Decimal, currency="USD", note="Auntie Jummy’s order"):
    client = get_client()
    amount_money = {"amount": int(Decimal(amount) * 100), "currency": currency}
    body = {
        "idempotency_key": f"order-{order_id}",
        "quick_pay": {
            "name": f"Auntie Jummy’s Order #{order_id}",
            "price_money": amount_money,
            "location_id": os.getenv("SQUARE_LOCATION_ID",""),
            "note": note,
        }
    }
    result = client.payment_links.create_payment_link(body)
    if result.is_success():
        return result.body["payment_link"]["url"]
    raise RuntimeError(str(result.errors))
