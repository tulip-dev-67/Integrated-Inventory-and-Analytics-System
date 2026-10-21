"""Part 3 analyses. OrderManager inherits these, so every method is role-gated
through the same _require() check and reads the same in-memory order list."""
from src.algorithms import heap_top_n, linear_search


class AnalysisMixin:

    # ---------- helpers ----------

    def _sales_orders(self):
        """Orders that count as sales. Cancelled orders are excluded because the
        dataset keeps an Amount on them even though Qty is 0 and nothing was sold."""
        return [o for o in self._orders if o.status != "Cancelled"]

    def _totals_by(self, group_attr, value_attr):
        totals = {}
        for o in self._sales_orders():
            key = getattr(o, group_attr)
            totals[key] = totals.get(key, 0) + getattr(o, value_attr)
        return totals

    # ---------- 1. Top sales ----------

    def top_products_by_amount(self, user, n=5):
        self._require(user, self.READ_ROLES)
        totals = self._totals_by("sku", "amount")
        return heap_top_n(list(totals.items()), n, key=lambda pair: pair[1])

    def top_products_by_qty(self, user, n=5):
        self._require(user, self.READ_ROLES)
        totals = self._totals_by("sku", "qty")
        return heap_top_n(list(totals.items()), n, key=lambda pair: pair[1])

    # ---------- 2. Sales by location ----------

    def sales_by_city(self, user, city):
        self._require(user, self.READ_ROLES)
        target = city.strip().upper()
        return sum(o.amount for o in self._sales_orders()
                   if o.ship_city.strip().upper() == target)

    def sales_by_state(self, user, state):
        self._require(user, self.READ_ROLES)
        target = state.strip().upper()
        return sum(o.amount for o in self._sales_orders()
                   if o.ship_state.strip().upper() == target)

    # ---------- 3. Order status ----------

    def status_counts(self, user):
        """Counts orders per Status using our linear search (as the brief asks)."""
        self._require(user, self.READ_ROLES)
        statuses = []
        for o in self._orders:
            if o.status not in statuses:
                statuses.append(o.status)
        counts = {}
        for s in statuses:
            counts[s] = len(linear_search(self._orders, lambda o, s=s: o.status == s))
        return counts

    # ---------- 4. Category performance ----------

    def category_totals(self, user):
        """Returns {category: (total_amount, total_qty)}."""
        self._require(user, self.READ_ROLES)
        amounts = self._totals_by("category", "amount")
        qtys = self._totals_by("category", "qty")
        return {c: (amounts[c], qtys[c]) for c in amounts}

    # ---------- 5. Order value ----------

    def order_values(self, user):
        """Total Amount per unique Order ID, summed across its line items."""
        self._require(user, self.READ_ROLES)
        return self._totals_by("order_id", "amount")

    def top_orders(self, user, n=5):
        self._require(user, self.READ_ROLES)
        totals = self._totals_by("order_id", "amount")
        return heap_top_n(list(totals.items()), n, key=lambda pair: pair[1])