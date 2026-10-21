from src.order_manager import OrderManager
from src.users import UserManager

users = UserManager()
users.create_user("junior", "pass456", "Junior Manager")
junior = users.authenticate("junior", "pass456")

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")

print("\nTop 5 SKUs by amount:")
for sku, total in m.top_products_by_amount(junior, 5):
    print(f"  {sku}: {total:,.2f}")

print("\nTop 5 SKUs by qty:")
for sku, total in m.top_products_by_qty(junior, 5):
    print(f"  {sku}: {total}")

print("\nSales in MUMBAI:", f"{m.sales_by_city(junior, 'mumbai'):,.2f}")
print("Sales in MAHARASHTRA:", f"{m.sales_by_state(junior, 'Maharashtra'):,.2f}")

print("\nOrders per status:")
for status, count in m.status_counts(junior).items():
    print(f"  {status}: {count}")

print("\nCategory (amount, qty):")
for cat, (amt, qty) in m.category_totals(junior).items():
    print(f"  {cat}: {amt:,.2f}, {qty}")

print("\nTop 5 orders by value:")
for oid, total in m.top_orders(junior, 5):
    print(f"  {oid}: {total:,.2f}")

print("\nUnique orders:", len(m.order_values(junior)))