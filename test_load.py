from src.order_manager import OrderManager

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")
print(len(m), "loaded;", len(m.skipped), "skipped;", len(m.warnings), "repaired")
print(m._orders[0])