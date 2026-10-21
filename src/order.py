from datetime import datetime


class Order:
    """One line item from the Amazon Sale Report."""

    def __init__(self, index, order_id, date, status, fulfilment, sales_channel,
                 ship_service_level, style, sku, category, size, asin,
                 courier_status, qty, currency, amount, ship_city, ship_state,
                 ship_postal_code, ship_country, promotion_ids, b2b, fulfilled_by):
        # Identifiers never change after creation, so they stay read-only.
        self.__index = index
        self.__order_id = order_id
        self.__sku = sku

        # Mutable fields are private and exposed through validated properties.
        self._date = date
        self._status = status
        self._qty = qty
        self._amount = amount

        self.fulfilment = fulfilment
        self.sales_channel = sales_channel
        self.ship_service_level = ship_service_level
        self.style = style
        self.category = category
        self.size = size
        self.asin = asin
        self.courier_status = courier_status
        self.currency = currency
        self.ship_city = ship_city
        self.ship_state = ship_state
        self.ship_postal_code = ship_postal_code
        self.ship_country = ship_country
        self.promotion_ids = promotion_ids  # list of strings
        self.b2b = b2b
        self.fulfilled_by = fulfilled_by

    @property
    def index(self):
        return self.__index

    @property
    def order_id(self):
        return self.__order_id

    @property
    def sku(self):
        return self.__sku

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        if not isinstance(value, datetime):
            raise ValueError("date must be a datetime object")
        self._date = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if not value or not value.strip():
            raise ValueError("status cannot be empty")
        self._status = value.strip()

    @property
    def qty(self):
        return self._qty

    @qty.setter
    def qty(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("qty must be a non-negative integer")
        self._qty = value

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        if value < 0:
            raise ValueError("amount cannot be negative")
        self._amount = float(value)

    def __str__(self):
        return (f"Order {self.order_id} | {self.date:%Y-%m-%d} | {self.status} | "
                f"SKU {self.sku} | {self.category} | Qty {self.qty} | "
                f"Amount {self.amount:.2f} | {self.ship_city}, {self.ship_state}")