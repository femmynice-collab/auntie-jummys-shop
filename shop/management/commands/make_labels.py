from django.core.management.base import BaseCommand
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import landscape
from shop.models import Order

# Brother QL "17mm x 54mm" approx: printable area ~ (54mm x 17mm)
LABEL_W = 54 * mm
LABEL_H = 17 * mm
MARGIN_X = 2 * mm
MARGIN_Y = 1 * mm

class Command(BaseCommand):
    help = "Generate a PDF of thermal labels (17x54mm) for an order's items."

    def add_arguments(self, parser):
        parser.add_argument('order_id', type=int)
        parser.add_argument('--out', default='labels.pdf')

    def handle(self, *args, **opts):
        order_id = opts['order_id']
        out = opts['out']
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            self.stderr.write("Order not found")
            return

        # Create a PDF where each page is one label
        from reportlab.lib.pagesizes import landscape
        c = canvas.Canvas(out, pagesize=(LABEL_W, LABEL_H))

        for it in order.items.all():
            name = it.product.name[:32]
            sku = (it.product.sku or "")[:20]
            upc = (it.product.upc or "")[:20]
            allergens = (it.product.allergens or "")[:40]

            # Draw a single label
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 9, name)
            c.setFont("Helvetica", 7)
            c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 9 - 9, f"SKU: {sku}  UPC: {upc}")
            if allergens:
                c.setFont("Helvetica-Oblique", 6)
                c.drawString(MARGIN_X, MARGIN_Y + 3, f"Allergens: {allergens}")
            # qty copies
            for _ in range(max(1, it.quantity - 1)):
                c.showPage()
                c.setFont("Helvetica-Bold", 9)
                c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 9, name)
                c.setFont("Helvetica", 7)
                c.drawString(MARGIN_X, LABEL_H - MARGIN_Y - 9 - 9, f"SKU: {sku}  UPC: {upc}")
                if allergens:
                    c.setFont("Helvetica-Oblique", 6)
                    c.drawString(MARGIN_X, MARGIN_Y + 3, f"Allergens: {allergens}")
            c.showPage()
        c.save()
        self.stdout.write(self.style.SUCCESS(f"Labels written to {out}"))
