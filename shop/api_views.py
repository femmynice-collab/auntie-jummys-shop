from django.http import JsonResponse, Http404
from .models import Product

def product_list(request):
    qs = Product.objects.filter(active=True).values('id','name','slug','price','stock','description','sales_count','featured')
    return JsonResponse(list(qs), safe=False)

def product_detail(request, slug):
    try:
        p = Product.objects.get(slug=slug, active=True)
    except Product.DoesNotExist:
        raise Http404
    data = {
        'id': p.id, 'name': p.name, 'slug': p.slug,
        'price': str(p.price), 'stock': p.stock,
        'description': p.description,
    }
    return JsonResponse(data)
