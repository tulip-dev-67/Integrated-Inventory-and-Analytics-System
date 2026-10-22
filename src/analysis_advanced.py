"""Part 3, items 6-9: cancellations, seasonality, inventory turnover, promotions."""
from src.algorithms import heap_top_n, merge_sort


def _is_cancelled(order):
    """Cancelled if either Status or Courier Status mentions cancellation."""
    return ("cancel" in order.status.lower()
            or "cancel" in order.courier_status.lower())


class AdvancedAnalysisMixin:

    @staticmethod
    def _month_key(order):
        return f"{order.date.year}-{order.date.month:02d}"

    @staticmethod
    def _quarter_key(order):
        return f"{order.date.year}-Q{(order.date.month - 1) // 3 + 1}"

    # ---------- 6. Cancellation frequency (stockout proxy) ----------
    # ASSUMPTION (put this in REPORT.md): the data records THAT an order was
    # cancelled, not WHY. We treat a high cancellation rate on one SKU as a
    # possible stockout signal. To confirm it we would need stock levels per SKU
    # over time, and a cancellation reason or initiator (seller vs customer).

    def cancelled_orders(self, user):
        self._require(user, self.READ_ROLES)
        return [o for o in self._orders if _is_cancelled(o)]

    def _cancellation_rates(self, group_attr):
        counts = {}
        for o in self._orders:
            key = getattr(o, group_attr)
            cancelled, total = counts.get(key, (0, 0))
            counts[key] = (cancelled + (1 if _is_cancelled(o) else 0), total + 1)
        return {k: (c, t, c / t) for k, (c, t) in counts.items()}

    def cancellation_by(self, user, group_attr):
        """Returns {sku or style: (cancelled, total, rate)}."""
        self._require(user, self.READ_ROLES)
        if group_attr not in ("sku", "style"):
            raise ValueError("group_attr must be 'sku' or 'style'.")
        return self._cancellation_rates(group_attr)

    def stockout_suspects(self, user, group_attr="sku", n=10, min_orders=30):
        """Highest cancellation rates, ignoring items with very few orders
        (a SKU with 1 order and 1 cancellation is 100% but means nothing)."""
        self._require(user, self.READ_ROLES)
        if group_attr not in ("sku", "style"):
            raise ValueError("group_attr must be 'sku' or 'style'.")
        rates = self._cancellation_rates(group_attr)
        eligible = [(k, v) for k, v in rates.items() if v[1] >= min_orders]
        return heap_top_n(eligible, n, key=lambda pair: pair[1][2])

    # ---------- 7. Seasonal patterns ----------

    def _volume_by(self, key_func):
        result = {}
        for o in self._sales_orders():
            k = key_func(o)
            orders, qty, amount = result.get(k, (0, 0, 0.0))
            result[k] = (orders + 1, qty + o.qty, amount + o.amount)
        return merge_sort(list(result.items()), key=lambda pair: pair[0])

    def volume_by_month(self, user):
        """Sorted list of (month, (order_lines, qty, amount))."""
        self._require(user, self.READ_ROLES)
        return self._volume_by(self._month_key)

    def volume_by_quarter(self, user):
        self._require(user, self.READ_ROLES)
        return self._volume_by(self._quarter_key)

    def peak_month_by(self, user, group_attr):
        """For each Category or Style: the month with the highest Qty."""
        self._require(user, self.READ_ROLES)
        if group_attr not in ("category", "style"):
            raise ValueError("group_attr must be 'category' or 'style'.")
        monthly = {}
        for o in self._sales_orders():
            months = monthly.setdefault(getattr(o, group_attr), {})
            m = self._month_key(o)
            months[m] = months.get(m, 0) + o.qty
        peaks = {}
        for group, months in monthly.items():
            best_month, best_qty = None, -1
            for m, q in months.items():
                if q > best_qty:
                    best_month, best_qty = m, q
            peaks[group] = (best_month, best_qty)
        return peaks

    # ---------- 8. Inventory turnover (simplified) ----------
    # PROXY (justify this in REPORT.md): there are no stock levels, so average
    # stock = peak monthly Qty for that SKU, i.e. we assume the seller holds
    # enough stock to cover its busiest month. Turnover = total Qty / peak.

    def inventory_turnover(self, user):
        """Returns {sku: (total_qty, peak_monthly_qty, turnover)}."""
        self._require(user, self.READ_ROLES)
        per_sku = {}
        for o in self._sales_orders():
            months = per_sku.setdefault(o.sku, {})
            m = self._month_key(o)
            months[m] = months.get(m, 0) + o.qty
        result = {}
        for sku, months in per_sku.items():
            total = sum(months.values())
            peak = max(months.values())
            if peak > 0:
                result[sku] = (total, peak, total / peak)
        return result

    def top_turnover(self, user, n=10, min_total_qty=20):
        self._require(user, self.READ_ROLES)
        table = self.inventory_turnover(user)
        eligible = [(k, v) for k, v in table.items() if v[0] >= min_total_qty]
        return heap_top_n(eligible, n, key=lambda pair: pair[1][2])

    # ---------- 9. Promotion analysis ----------

    def promotion_stats(self, user, n=5):
        """Top n promotions by number of distinct orders. An order with two
        promotions counts toward both, so totals across promotions overlap."""
        self._require(user, self.READ_ROLES)
        promos = {}
        for o in self._sales_orders():
            for p in o.promotion_ids:
                entry = promos.setdefault(
                    p, {"orders": set(), "sales": 0.0, "categories": {}})
                entry["orders"].add(o.order_id)
                entry["sales"] += o.amount
                cats = entry["categories"]
                cats[o.category] = cats.get(o.category, 0.0) + o.amount
        top = heap_top_n(list(promos.items()), n,
                         key=lambda pair: len(pair[1]["orders"]))
        report = []
        for promo, e in top:
            top_cats = heap_top_n(list(e["categories"].items()), 3,
                                  key=lambda pair: pair[1])
            report.append({"promotion": promo, "orders": len(e["orders"]),
                           "sales": e["sales"], "top_categories": top_cats})
        return report