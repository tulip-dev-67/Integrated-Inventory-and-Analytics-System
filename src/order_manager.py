from datetime import datetime
from src.order import Order

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


class OrderManager:
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