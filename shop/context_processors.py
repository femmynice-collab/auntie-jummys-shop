def cart(request):
    return {'cart': request.session.get('cart', {})}
