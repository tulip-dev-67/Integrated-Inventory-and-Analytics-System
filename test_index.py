import time
from src.order_manager import OrderManager
from src.users import UserManager

users = UserManager()
users.create_user("boss", "pass123", "Manager")
users.create_user("junior", "pass456", "Junior Manager")
boss = users.authenticate("boss", "pass123")
junior = users.authenticate("junior", "pass456")

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")

# 1. Hash index vs linear search for MUMBAI
t = time.time(); linear = m.search_orders(junior, "ship_city", "MUMBAI"); t_linear = time.time() - t
m.find_by_city(junior, "MUMBAI")  # first call builds the index
t = time.time(); hashed = m.find_by_city(junior, "MUMBAI"); t_hash = time.time() - t
print(f"MUMBAI: linear={len(linear)} in {t_linear:.4f}s | hash={len(hashed)} in {t_hash:.6f}s")

# 2. Binary search vs linear search by Order ID
target = m._orders[5000].order_id
t = time.time(); linear = m.search_orders(junior, "order_id", target); t_linear = time.time() - t
m.find_by_order_id(junior, target)  # first call sorts and caches
t = time.time(); binary = m.find_by_order_id(junior, target); t_bin = time.time() - t
print(f"Order {target}: linear={len(linear)} in {t_linear:.4f}s | binary={len(binary)} in {t_bin:.6f}s")

# 3. Binary search + hash filter by status
print("Order + status:", len(m.find_by_order_id_and_status(junior, target, binary[0].status)))

# 4. SKU lookup
sku = m._orders[100].sku
print(f"SKU {sku}: {len(m.find_by_sku(junior, sku))} orders")

# 5. Indexes stay correct after an edit
m.edit_order(boss, m._orders[0].index, ship_city="TESTVILLE")
print("After edit, TESTVILLE orders:", len(m.find_by_city(junior, "TESTVILLE")))  # expect 1