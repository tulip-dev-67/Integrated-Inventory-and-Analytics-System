from src.order_manager import OrderManager
from src.users import UserManager

users = UserManager()
users.create_user("junior", "pass456", "Junior Manager")
junior = users.authenticate("junior", "pass456")

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")

dates = [o.date for o in m._orders]
print("Date range:", min(dates).date(), "to", max(dates).date())

print("\nCancelled order lines:", len(m.cancelled_orders(junior)))

print("\nTop 5 stockout-suspect SKUs (cancelled, total, rate):")
for sku, (c, t, r) in m.stockout_suspects(junior, "sku", 5):
    print(f"  {sku}: {c}/{t} = {r:.1%}")

print("\nTop 5 stockout-suspect Styles:")
for style, (c, t, r) in m.stockout_suspects(junior, "style", 5):
    print(f"  {style}: {c}/{t} = {r:.1%}")

print("\nVolume by month (lines, qty, amount):")
for month, (n, q, a) in m.volume_by_month(junior):
    print(f"  {month}: {n}, {q}, {a:,.2f}")

print("\nVolume by quarter:")
for quarter, (n, q, a) in m.volume_by_quarter(junior):
    print(f"  {quarter}: {n}, {q}, {a:,.2f}")

print("\nPeak month per category:")
for cat, (month, q) in m.peak_month_by(junior, "category").items():
    print(f"  {cat}: {month} ({q} units)")

print("\nTop 5 SKUs by turnover (total, peak month, ratio):")
for sku, (t, p, r) in m.top_turnover(junior, 5):
    print(f"  {sku}: {t}, {p}, {r:.2f}")

print("\nTop 5 promotions:")
for p in m.promotion_stats(junior, 5):
    print(f"  {p['promotion'][:60]}... orders={p['orders']} sales={p['sales']:,.2f}")
    print("     top categories:", [c for c, _ in p["top_categories"]])