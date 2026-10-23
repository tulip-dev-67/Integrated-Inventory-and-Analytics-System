"""Matplotlib charts. matplotlib only draws: every number plotted is computed
by our own code in OrderManager."""
import os
import matplotlib
matplotlib.use("Agg")  # draw straight to image files, no pop-up window needed
import matplotlib.pyplot as plt

from src.algorithms import heap_top_n, merge_sort


class ChartMaker:
    def __init__(self, manager, user, output_dir="charts"):
        self._m = manager
        self._user = user
        self._dir = output_dir
        os.makedirs(self._dir, exist_ok=True)

    def _save(self, filename):
        path = os.path.join(self._dir, filename)
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def sales_by_state(self, n=15):
        """Bar chart of the n states with the highest total sales."""
        totals = self._m.totals_by_group(self._user, "ship_state", "amount")
        top = heap_top_n(list(totals.items()), n, key=lambda pair: pair[1])
        names = [state for state, _ in top]
        values = [total / 1_000_000 for _, total in top]
        plt.figure(figsize=(10, 6))
        plt.bar(names, values, color="steelblue")
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Total sales (million INR)")
        plt.title(f"Total sales by ship-state (top {n})")
        return self._save("sales_by_state.png")

    def status_pie(self):
        """Pie chart of order status. Slices under 2% are merged into 'Other'."""
        counts = self._m.status_counts(self._user)
        total = sum(counts.values())
        ranked = merge_sort(list(counts.items()), key=lambda pair: pair[1], reverse=True)
        labels, values, other = [], [], 0
        for status, count in ranked:
            if count / total >= 0.02:
                labels.append(status)
                values.append(count)
            else:
                other += count
        if other:
            labels.append("Other")
            values.append(other)
        plt.figure(figsize=(8, 6))
        plt.pie(values, autopct="%1.1f%%", startangle=90)
        plt.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5))
        plt.title("Distribution of order status")
        return self._save("status_pie.png")

    def sales_by_category(self):
        """Bar chart of total sales per category, highest first."""
        table = self._m.category_totals(self._user)
        ranked = merge_sort(list(table.items()), key=lambda pair: pair[1][0], reverse=True)
        names = [c for c, _ in ranked]
        values = [amount / 1_000_000 for _, (amount, _qty) in ranked]
        plt.figure(figsize=(9, 6))
        plt.bar(names, values, color="seagreen")
        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Total sales (million INR)")
        plt.title("Total sales by category")
        return self._save("sales_by_category.png")

    def sales_over_time(self):
        """Line chart of sales per month, using the month taken from Date."""
        monthly = self._m.volume_by_month(self._user)
        months = [m for m, _ in monthly]
        values = [amount / 1_000_000 for _, (_n, _q, amount) in monthly]
        plt.figure(figsize=(8, 5))
        plt.plot(months, values, marker="o", color="darkorange")
        plt.ylabel("Total sales (million INR)")
        plt.title("Sales by month (March has only one day of data)")
        return self._save("sales_over_time.png")

    def make_all(self):
        return [self.sales_by_state(), self.status_pie(),
                self.sales_by_category(), self.sales_over_time()]