import time
from src.algorithms import quick_sort, merge_sort, heap_top_n, binary_search_first, HashIndex
from src.order_manager import OrderManager
from src.users import UserManager

# Small checks first: you can verify these by eye.
nums = [5, 3, 8, 1, 9, 2, 8]
print("quick sort :", quick_sort(nums, key=lambda x: x))              # [1, 2, 3, 5, 8, 8, 9]
print("merge sort :", merge_sort(nums, key=lambda x: x, reverse=True)) # [9, 8, 8, 5, 3, 2, 1]
print("top 3      :", heap_top_n(nums, 3, key=lambda x: x))            # [9, 8, 8]
print("binary srch:", binary_search_first([1, 2, 3, 5, 8, 8, 9], 8, key=lambda x: x))  # 4
print("hash index :", HashIndex(nums, key=lambda x: x % 2).get(0))    # [8, 2, 8]

# Now the real data.
users = UserManager()
users.create_user("junior", "pass456", "Junior Manager")
junior = users.authenticate("junior", "pass456")

m = OrderManager()
m.load_orders("data/Amazon Sale Report.csv")

start = time.time()
by_amount = m.sort_orders(junior, "amount", descending=True)
print(f"merge sort on {len(by_amount)} orders took {time.time() - start:.2f}s")
print("highest amount:", by_amount[0])

start = time.time()
by_qty = quick_sort(m._orders, key=lambda o: o.qty)
print(f"quick sort on {len(by_qty)} orders took {time.time() - start:.2f}s")

print("cancelled orders:", len(m.find_cancelled(junior)))