"""Command-line interface: log in, then use the menu your role allows."""
import sys

from src.order import Order
from src.order_manager import OrderManager, parse_date
from src.users import (UserManager, AuthenticationError, PermissionDenied,
                       MANAGER, JUNIOR_MANAGER)
from src.charts import ChartMaker

DEFAULT_PATH = "data/Amazon Sale Report.csv"


class CLI:
    def __init__(self, data_path):
        self._path = data_path
        self._orders = OrderManager()
        self._user = None
        # Demo accounts, held in memory only (see README).
        self._users = UserManager()
        self._users.create_user("manager", "manager123", MANAGER)
        self._users.create_user("junior", "junior123", JUNIOR_MANAGER)

    # ---------- start-up ----------

    def load_data(self):
        print(f"Loading {self._path} ...")
        try:
            self._orders.load_orders(self._path)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Put the CSV in the data folder, or run: python main.py <path to csv>")
            return False
        except (ValueError, KeyError) as e:
            print(f"Error: the file could not be read ({e}).")
            return False
        self.show_load_summary()
        return True

    def show_load_summary(self):
        o = self._orders
        print(f"\nLoaded {len(o)} orders | skipped {len(o.skipped)} | repaired {len(o.warnings)}")
        for line_no, reason in o.skipped[:5]:
            print(f"  skipped line {line_no}: {reason}")
        for line_no, reason in o.warnings[:3]:
            print(f"  repaired line {line_no}: {reason}")
        if len(o.warnings) > 3:
            print(f"  ... and {len(o.warnings) - 3} more repaired rows")

    def login(self):
        for attempt in range(3):
            username = input("Username: ").strip()
            password = input("Password: ")
            try:
                self._user = self._users.authenticate(username, password)
                print(f"Welcome, {self._user.username} ({self._user.role}).")
                return True
            except AuthenticationError as e:
                print(f"Login failed: {e} ({2 - attempt} attempts left)")
        return False

    # ---------- menu ----------

    def _menu_items(self):
        items = [
            ("Search orders", self.search),
            ("Sort orders", self.sort),
            ("Run an analysis", self.analysis_menu),
            ("Create charts", self.charts),
            ("Show data-loading summary", self.show_load_summary),
        ]
        if self._user.role == MANAGER:  # Junior Managers never see these
            items += [("Add an order", self.add),
                      ("Edit an order", self.edit),
                      ("Delete an order", self.delete)]
        return items

    def main_loop(self):
        while True:
            items = self._menu_items()
            print(f"\n=== Main menu ({self._user.username}, {self._user.role}) ===")
            for i, (label, _) in enumerate(items, 1):
                print(f"{i}. {label}")
            print("0. Log out")
            choice = input("Choose: ").strip()
            if choice == "0":
                return
            if not choice.isdigit() or not 1 <= int(choice) <= len(items):
                print("Invalid choice.")
                continue
            self._run_safely(items[int(choice) - 1][1])

    @staticmethod
    def _run_safely(handler):
        """Any error becomes a clear message, never a crash."""
        try:
            handler()
        except PermissionDenied as e:
            print(f"Permission denied: {e}")
        except (ValueError, KeyError) as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    # ---------- input helpers ----------

    @staticmethod
    def _pick(title, options):
        print(title)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        raw = input("Choose: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        raise ValueError("Invalid choice.")

    @staticmethod
    def _ask_int(prompt, minimum=None):
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f"'{raw}' is not a whole number.")
        if minimum is not None and value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        return value

    @staticmethod
    def _ask_float(prompt, minimum=None):
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            raise ValueError(f"'{raw}' is not a number.")
        if minimum is not None and value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        return value

    @staticmethod
    def _ask_n(default=5):
        raw = input(f"How many results (N)? [{default}]: ").strip()
        if raw == "":
            return default
        if not raw.isdigit() or int(raw) < 1:
            raise ValueError("N must be a positive whole number.")
        return int(raw)

    @staticmethod
    def _show_orders(orders, limit=10):
        print(f"{len(orders)} order(s) found.")
        for order in orders[:limit]:
            print("  ", order)
        if len(orders) > limit:
            print(f"   ... and {len(orders) - limit} more")

    # ---------- search and sort ----------

    def search(self):
        field = self._pick("Search by:", list(OrderManager.SEARCH_FIELDS))
        value = input(f"Value for {field}: ").strip()
        if not value:
            raise ValueError("Search value cannot be empty.")
        user = self._user
        if field == "order_id":
            results = self._orders.find_by_order_id(user, value)      # binary search
        elif field == "ship_city":
            results = self._orders.find_by_city(user, value)          # hash index
        else:
            results = self._orders.search_orders(user, field, value)  # linear search
        self._show_orders(results)

    def sort(self):
        field = self._pick("Sort by:", list(OrderManager.SORT_FIELDS))
        direction = self._pick("Direction:", ["Ascending", "Descending"])
        print("Sorting (this takes a few seconds)...")
        results = self._orders.sort_orders(self._user, field, direction == "Descending")
        self._show_orders(results)

    # ---------- analyses ----------

    def analysis_menu(self):
        options = {
            "Top products by amount": self._an_top_amount,
            "Top products by quantity": self._an_top_qty,
            "Sales for a city": self._an_city,
            "Sales for a state": self._an_state,
            "Orders per status": self._an_status,
            "Category totals": self._an_category,
            "Top orders by value": self._an_top_orders,
            "Cancellation rates (stockout proxy)": self._an_cancellation,
            "Monthly and quarterly volume": self._an_seasonal,
            "Peak month per category": self._an_peak,
            "Inventory turnover": self._an_turnover,
            "Promotion analysis": self._an_promotions,
        }
        choice = self._pick("Analysis:", list(options))
        options[choice]()

    def _an_top_amount(self):
        for sku, total in self._orders.top_products_by_amount(self._user, self._ask_n()):
            print(f"  {sku}: {total:,.2f}")

    def _an_top_qty(self):
        for sku, total in self._orders.top_products_by_qty(self._user, self._ask_n()):
            print(f"  {sku}: {total}")

    def _an_city(self):
        city = input("City: ").strip()
        print(f"Total sales for {city.upper()}: {self._orders.sales_by_city(self._user, city):,.2f}")

    def _an_state(self):
        state = input("State: ").strip()
        print(f"Total sales for {state.upper()}: {self._orders.sales_by_state(self._user, state):,.2f}")

    def _an_status(self):
        for status, count in self._orders.status_counts(self._user).items():
            print(f"  {status}: {count}")

    def _an_category(self):
        for cat, (amount, qty) in self._orders.category_totals(self._user).items():
            print(f"  {cat}: amount {amount:,.2f}, qty {qty}")

    def _an_top_orders(self):
        for oid, total in self._orders.top_orders(self._user, self._ask_n()):
            print(f"  {oid}: {total:,.2f}")

    def _an_cancellation(self):
        total = len(self._orders.cancelled_orders(self._user))
        print(f"Cancelled order lines: {total} of {len(self._orders)}")
        print("Assumption: a high rate on one SKU may signal a stockout (the data gives no reason).")
        for group in ("sku", "style"):
            print(f"Highest {group} cancellation rates (min 30 orders):")
            for key, (c, t, r) in self._orders.stockout_suspects(self._user, group, self._ask_n()):
                print(f"  {key}: {c}/{t} = {r:.1%}")

    def _an_seasonal(self):
        print("By month (order lines, qty, amount):")
        for month, (n, q, a) in self._orders.volume_by_month(self._user):
            print(f"  {month}: {n}, {q}, {a:,.2f}")
        print("By quarter:")
        for quarter, (n, q, a) in self._orders.volume_by_quarter(self._user):
            print(f"  {quarter}: {n}, {q}, {a:,.2f}")

    def _an_peak(self):
        group = self._pick("Group by:", ["category", "style"])
        peaks = self._orders.peak_month_by(self._user, group)
        for name, (month, qty) in list(peaks.items())[:25]:
            print(f"  {name}: {month} ({qty} units)")
        if len(peaks) > 25:
            print(f"  ... {len(peaks) - 25} more")

    def _an_turnover(self):
        print("Turnover = total qty / peak monthly qty (max 3.00 with 3 months of data)")
        for sku, (t, p, r) in self._orders.top_turnover(self._user, self._ask_n()):
            print(f"  {sku}: total {t}, peak month {p}, ratio {r:.2f}")

    def _an_promotions(self):
        for p in self._orders.promotion_stats(self._user, self._ask_n()):
            cats = ", ".join(c for c, _ in p["top_categories"])
            print(f"  {p['promotion'][:70]}")
            print(f"     orders {p['orders']}, sales {p['sales']:,.2f}, top categories: {cats}")

    # ---------- charts ----------

    def charts(self):
        print("Drawing charts ...")
        for path in ChartMaker(self._orders, self._user).make_all():
            print("  saved", path)

    # ---------- manager-only actions ----------

    def add(self):
        existing = [int(o.index) for o in self._orders._orders if o.index.isdigit()]
        index = str(max(existing) + 1 if existing else 0)
        order_id = input("Order ID: ").strip()
        date = parse_date(input("Date (e.g. 05-31-22): "))
        status = input("Status: ").strip()
        sku = input("SKU: ").strip()
        category = input("Category: ").strip()
        qty = self._ask_int("Qty: ", minimum=0)
        amount = self._ask_float("Amount: ", minimum=0)
        city = input("Ship city: ").strip().upper()
        state = input("Ship state: ").strip().upper()
        if not order_id or not status or not sku:
            raise ValueError("Order ID, Status and SKU cannot be empty.")
        order = Order(index=index, order_id=order_id, date=date, status=status,
                      fulfilment="", sales_channel="", ship_service_level="",
                      style="", sku=sku, category=category, size="", asin="",
                      courier_status="", qty=qty, currency="INR", amount=amount,
                      ship_city=city, ship_state=state, ship_postal_code="",
                      ship_country="IN", promotion_ids=[], b2b="FALSE",
                      fulfilled_by="")
        self._orders.add_order(self._user, order)
        print(f"Order added with index {index}.")

    def edit(self):
        index = input("Index of the order to edit: ").strip()
        field = self._pick("Field to change:", list(OrderManager.EDITABLE_FIELDS))
        raw = input(f"New value for {field}: ").strip()
        if field == "qty":
            value = self._ask_int_from(raw, minimum=0)
        elif field == "amount":
            value = self._ask_float_from(raw, minimum=0)
        elif field == "date":
            value = parse_date(raw)
        elif field in ("ship_city", "ship_state"):
            value = raw.upper()
        else:
            value = raw
        self._orders.edit_order(self._user, index, **{field: value})
        print("Order updated.")

    @staticmethod
    def _ask_int_from(raw, minimum=None):
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f"'{raw}' is not a whole number.")
        if minimum is not None and value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        return value

    @staticmethod
    def _ask_float_from(raw, minimum=None):
        try:
            value = float(raw)
        except ValueError:
            raise ValueError(f"'{raw}' is not a number.")
        if minimum is not None and value < minimum:
            raise ValueError(f"Value must be at least {minimum}.")
        return value

    def delete(self):
        index = input("Index of the order to delete: ").strip()
        if input(f"Delete order {index}? This cannot be undone (y/n): ").strip().lower() != "y":
            print("Cancelled.")
            return
        self._orders.delete_order(self._user, index)
        print("Order deleted.")


def run():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    cli = CLI(path)
    try:
        if not cli.load_data():
            return
        while True:
            print("\n--- Login (demo accounts are listed in the README) ---")
            if not cli.login():
                print("Too many failed attempts. Goodbye.")
                return
            cli.main_loop()
            if input("\nLog in as another user? (y/n): ").strip().lower() != "y":
                print("Goodbye.")
                return
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")