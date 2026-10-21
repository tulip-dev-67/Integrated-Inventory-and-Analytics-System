from src.users import MANAGER, JUNIOR_MANAGER, PermissionDenied
from datetime import datetime
from src.order import Order
from src.algorithms import merge_sort, linear_search
from src.analysis import AnalysisMixin

DATE_FORMATS = ["%m-%d-%y", "%m-%d-%Y", "%Y-%m-%d"]


def split_csv_line(line):
    """Split one CSV line on commas, respecting double-quoted fields."""
    fields, current, in_quotes = [], [], False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':  # escaped quote
                    current.append('"')
                    i += 1
                else:
                    in_quotes = False
            else:
                current.append(ch)
        elif ch == '"':
            in_quotes = True
        elif ch == ",":
            fields.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    fields.append("".join(current))
    return fields


def parse_date(text):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognised date '{text}'")


class OrderManager(AnalysisMixin):
    def __init__(self):
        self._orders = []
        self.skipped = []   # (line number, reason)
        self.warnings = []  # rows kept but repaired

    def load_orders(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {path}")

        if not lines:
            raise ValueError("Data file is empty")

        header = [h.strip() for h in split_csv_line(lines[0])]
        # Drop unnamed columns (the trailing empty one) explicitly.
        keep = [i for i, name in enumerate(header) if name != ""]
        names = [header[i] for i in keep]
        col = {name: pos for pos, name in enumerate(names)}

        for line_no, line in enumerate(lines[1:], start=2):
            if not line.strip():
                continue
            raw = split_csv_line(line)
            if len(raw) < max(keep) + 1:
                self.skipped.append((line_no, "too few columns"))
                continue
            row = [raw[i].strip() for i in keep]

            try:
                date = parse_date(row[col["Date"]])
            except ValueError as e:
                self.skipped.append((line_no, f"malformed date: {e}"))
                continue

            try:
                qty = int(row[col["Qty"]])
            except ValueError:
                self.skipped.append((line_no, "missing or invalid Qty"))
                continue

            amount_text = row[col["Amount"]]
            if amount_text == "":
                amount = 0.0
                self.warnings.append((line_no, "Amount missing, set to 0.0"))
            else:
                try:
                    amount = float(amount_text)
                except ValueError:
                    self.skipped.append((line_no, "invalid Amount"))
                    continue

            promos = [p.strip() for p in row[col["promotion-ids"]].split(",") if p.strip()]

            self._orders.append(Order(
                index=row[col["index"]], order_id=row[col["Order ID"]], date=date,
                status=row[col["Status"]], fulfilment=row[col["Fulfilment"]],
                sales_channel=row[col["Sales Channel"]],
                ship_service_level=row[col["ship-service-level"]],
                style=row[col["Style"]], sku=row[col["SKU"]],
                category=row[col["Category"]], size=row[col["Size"]],
                asin=row[col["ASIN"]], courier_status=row[col["Courier Status"]],
                qty=qty, currency=row[col["currency"]], amount=amount,
                ship_city=row[col["ship-city"]], ship_state=row[col["ship-state"]],
                ship_postal_code=row[col["ship-postal-code"]],
                ship_country=row[col["ship-country"]], promotion_ids=promos,
                b2b=row[col["B2B"]], fulfilled_by=row[col["fulfilled-by"]],
            ))

    def __len__(self):
        return len(self._orders)

    READ_ROLES = (MANAGER, JUNIOR_MANAGER)
    WRITE_ROLES = (MANAGER,)
    EDITABLE_FIELDS = ("status", "qty", "amount", "date", "courier_status",
                       "ship_city", "ship_state")
    SEARCH_FIELDS = ("order_id", "status", "category", "ship_city")

    def _require(self, user, allowed_roles):
        """Every public operation calls this first."""
        if user is None:
            raise PermissionDenied("Login required.")
        if user.role not in allowed_roles:
            raise PermissionDenied(f"{user.role} is not allowed to perform this action.")

    def _find_by_index(self, index):
        for order in self._orders:
            if order.index == str(index):
                return order
        return None

    def add_order(self, user, order):
        self._require(user, self.WRITE_ROLES)
        if self._find_by_index(order.index) is not None:
            raise ValueError(f"An order with index {order.index} already exists.")
        self._orders.append(order)

    def edit_order(self, user, index, **changes):
        self._require(user, self.WRITE_ROLES)
        order = self._find_by_index(index)
        if order is None:
            raise ValueError(f"No order with index {index}.")
        for field in changes:
            if field not in self.EDITABLE_FIELDS:
                raise ValueError(f"Field '{field}' cannot be edited.")
        for field, value in changes.items():
            setattr(order, field, value)

    def delete_order(self, user, index):
        self._require(user, self.WRITE_ROLES)
        order = self._find_by_index(index)
        if order is None:
            raise ValueError(f"No order with index {index}.")
        self._orders.remove(order)

    def search_orders(self, user, field, value):
        """Linear search; we replace this with a hash index later."""
        self._require(user, self.READ_ROLES)
        if field not in self.SEARCH_FIELDS:
            raise ValueError(f"Cannot search by '{field}'. Choose from {self.SEARCH_FIELDS}.")
        target = str(value).strip().lower()
        results = []
        for order in self._orders:
            if str(getattr(order, field)).strip().lower() == target:
                results.append(order)
        return results

    SORT_FIELDS = ("date", "amount", "qty")

    def sort_orders(self, user, field, descending=False):
        """Return a new sorted list. Uses our stable merge sort, so sorting
        by Date and then by another field keeps earlier ordering for ties."""
        self._require(user, self.READ_ROLES)
        if field not in self.SORT_FIELDS:
            raise ValueError(f"Cannot sort by '{field}'. Choose from {self.SORT_FIELDS}.")
        return merge_sort(self._orders, key=lambda o: getattr(o, field), reverse=descending)

    def find_cancelled(self, user):
        """Linear search for every order with Status 'Cancelled'."""
        self._require(user, self.READ_ROLES)
        return linear_search(self._orders, lambda o: o.status == "Cancelled")