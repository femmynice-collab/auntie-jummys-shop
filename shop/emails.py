from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_order_received(order):
    subject = f"Order #{order.id} received — Auntie Jummy’s"
    body = render_to_string("emails/order_received.txt", {"order": order})
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
    if getattr(settings, "ORDER_NOTIFY_EMAIL", None):
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.ORDER_NOTIFY_EMAIL], fail_silently=True)

def send_payment_confirmed(order):
    subject = f"Payment confirmed for Order #{order.id} — Auntie Jummy’s"
    body = render_to_string("emails/payment_confirmed.txt", {"order": order})
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)
    if getattr(settings, "ORDER_NOTIFY_EMAIL", None):
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.ORDER_NOTIFY_EMAIL], fail_silently=True)
