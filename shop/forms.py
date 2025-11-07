from django import forms

class CheckoutForm(forms.Form):
    FULFILLMENT = (('delivery','Delivery'),('pickup','Local Pickup'))
    name = forms.CharField(max_length=120, label="Full Name")
    email = forms.EmailField()
    address = forms.CharField(max_length=250)
    city = forms.CharField(max_length=120)
    state = forms.CharField(max_length=100)
    zip_code = forms.CharField(max_length=20)
    delivery_notes = forms.CharField(max_length=300, required=False)
    promo_code = forms.CharField(max_length=40, required=False, label="Promo code")
    fulfillment_method = forms.ChoiceField(choices=FULFILLMENT, initial='delivery')
    pickup_note = forms.CharField(max_length=140, required=False)
    pickup_slot = forms.ChoiceField(choices=[], required=False, label='Pickup time (if pickup)')
