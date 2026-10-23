from src.order_manager import OrderManager
from src.users import UserManager
from src.charts import ChartMaker

users = UserManager()
users.create_user("junior", "pass456", "Junior Manager")
junior = users.authenticate("junior", "pass456")

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")

for path in ChartMaker(m, junior).make_all():
    print("saved", path)