"""Fast lookups: binary search by Order ID, hash indexes by SKU and ship-city.
Indexes are built once, on first use, and thrown away whenever the data changes."""
from src.algorithms import merge_sort, binary_search_first, HashIndex


class IndexMixin:

    def _invalidate_indexes(self):
        """Called after add / edit / delete, so no lookup uses stale data."""
        self._index_cache = {}

    def _get_index(self, name, builder):
        cache = getattr(self, "_index_cache", None)
        if cache is None:
            cache = self._index_cache = {}
        if name not in cache:
            cache[name] = builder()
        return cache[name]

    def _sorted_by_order_id(self):
        # Binary search only works on sorted data, so sort once and keep the result.
        return self._get_index(
            "sorted_order_id",
            lambda: merge_sort(self._orders, key=lambda o: o.order_id))

    def _sku_index(self):
        return self._get_index(
            "sku", lambda: HashIndex(self._orders, key=lambda o: o.sku))

    def _city_index(self):
        # Keys are upper-cased so "mumbai" and "MUMBAI" find the same entry.
        return self._get_index(
            "city",
            lambda: HashIndex(self._orders, key=lambda o: o.ship_city.strip().upper()))

    def find_by_order_id(self, user, order_id):
        """Binary search by Order ID. One order can have several line items,
        so after finding the first match we walk right while the ID still matches."""
        self._require(user, self.READ_ROLES)
        target = order_id.strip()
        ordered = self._sorted_by_order_id()
        pos = binary_search_first(ordered, target, key=lambda o: o.order_id)
        results = []
        if pos == -1:
            return results
        while pos < len(ordered) and ordered[pos].order_id == target:
            results.append(ordered[pos])
            pos += 1
        return results

    def find_by_sku(self, user, sku):
        """Hash lookup by SKU."""
        self._require(user, self.READ_ROLES)
        return self._sku_index().get(sku.strip())

    def find_by_city(self, user, city):
        """Hash lookup by ship-city, e.g. all orders shipped to MUMBAI."""
        self._require(user, self.READ_ROLES)
        return self._city_index().get(city.strip().upper())

    def find_by_order_id_and_status(self, user, order_id, status):
        """Binary search narrows 128k orders to the few with this Order ID,
        then a small hash index on Status picks the ones we want."""
        self._require(user, self.READ_ROLES)
        matches = self.find_by_order_id(user, order_id)
        return HashIndex(matches, key=lambda o: o.status).get(status)