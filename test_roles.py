from src.order_manager import OrderManager
from src.users import UserManager, PermissionDenied, AuthenticationError

users = UserManager()
users.create_user("boss", "pass123", "Manager")
users.create_user("junior", "pass456", "Junior Manager")

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")

boss = users.authenticate("boss", "pass123")
junior = users.authenticate("junior", "pass456")

print("Junior search:", len(m.search_orders(junior, "status", "Cancelled")), "cancelled orders")

try:
    m.delete_order(junior, 0)
except PermissionDenied as e:
    print("Junior delete blocked:", e)

try:
    m.search_orders(None, "status", "Cancelled")
except PermissionDenied as e:
    print("Anonymous blocked:", e)

try:
    users.authenticate("boss", "wrong")
except AuthenticationError as e:
    print("Bad login:", e)

m.edit_order(boss, 0, status="Shipped")
print("Manager edit:", m.search_orders(boss, "order_id", "405-8078784-5731545")[0])
m.delete_order(boss, 0)
print("Orders after delete:", len(m))