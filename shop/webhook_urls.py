from django.urls import path
from .webhooks import square_payment_webhook
urlpatterns = [ path('', square_payment_webhook, name='square_payment_webhook') ]
