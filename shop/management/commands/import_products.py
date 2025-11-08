# shop/management/commands/import_products.py
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from shop.models import Product, Category

class Command(BaseCommand):
    help = "Import products from a CSV/Excel-export. Creates categories if needed."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to CSV in your repo (e.g., data/inventory.csv)")
        parser.add_argument("--name-col", default="item_name")
        parser.add_argument("--price-col", default="default_price")
        parser.add_argument("--cat-col", default="category_l2")
        parser.add_argument("--stock-col", default=None)  # if your sheet has qty
        parser.add_argument("--desc-col", default=None)
        parser.add_argument("--sku-col", default="sku_id")
        parser.add_argument("--upc-col", default="upc_id")
        parser.add_argument("--default-stock", type=int, default=25)
        parser.add_argument("--encoding", default="utf-8")
        parser.add_argument("--delimiter", default=",")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        path = opts["csv_path"]
        name_col = opts["name_col"]
        price_col = opts["price_col"]
        cat_col = opts["cat_col"]
        stock_col = opts["stock_col"]
        desc_col = opts["desc_col"]
        sku_col = opts["sku_col"]
        upc_col = opts["upc_col"]
        default_stock = opts["default_stock"]

        created, updated, skipped = 0, 0, 0

        try:
            with open(path, "r", encoding=opts["encoding"], newline="") as f:
                reader = csv.DictReader(f, delimiter=opts["delimiter"])
                missing = [c for c in (name_col, price_col) if c not in reader.fieldnames]
                if missing:
                    raise CommandError(f"Missing required columns in CSV: {missing}")

                for row in reader:
                    name = (row.get(name_col) or "").strip()
                    if not name:
                        skipped += 1
                        continue

                    # price
                    raw_price = str(row.get(price_col) or "0").strip().replace("$","")
                    try:
                        price = Decimal(raw_price)
                    except Exception:
                        self.stderr.write(f"Bad price for {name!r}: {raw_price!r} -> skipping")
                        skipped += 1
                        continue

                    # category
                    cat_name = (row.get(cat_col) or row.get("category_l1") or "Uncategorized").strip() if cat_col else "Uncategorized"
                    cat_slug = slugify(cat_name) or "uncategorized"
                    category, _ = Category.objects.get_or_create(name=cat_name, defaults={"slug": cat_slug})

                    # existing product?
                    prod = Product.objects.filter(name__iexact=name).first()
                    is_new = False
                    if not prod:
                        prod = Product(name=name, slug=slugify(name)[:100] or None, category=category)
                        is_new = True
                    else:
                        # update category if changed
                        if category and prod.category_id != category.id:
                            prod.category = category

                    prod.price = price

                    # stock
                    if stock_col and row.get(stock_col):
                        try:
                            prod.stock = int(str(row[stock_col]).strip())
                        except Exception:
                            prod.stock = default_stock
                    else:
                        prod.stock = default_stock

                    # optional fields if your model has them (we added earlier)
                    if hasattr(prod, "sku") and sku_col:
                        prod.sku = (row.get(sku_col) or "").strip()
                    if hasattr(prod, "upc") and upc_col:
                        prod.upc = (row.get(upc_col) or "").strip()
                    if hasattr(prod, "allergens"):
                        prod.allergens = prod.allergens or ""

                    # description (optional)
                    if desc_col:
                        prod.description = (row.get(desc_col) or "").strip()

                    if opts["dry_run"]:
                        self.stdout.write(f"DRY-RUN: {'CREATE' if is_new else 'UPDATE'} {name} ${price} stock={prod.stock} cat={category.name}")
                    else:
                        prod.save()
                        if is_new:
                            created += 1
                        else:
                            updated += 1

        except FileNotFoundError:
            raise CommandError(f"CSV not found at {path}. Did you upload it to the repo?")

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Updated: {updated}, Skipped: {skipped}"
        ))
