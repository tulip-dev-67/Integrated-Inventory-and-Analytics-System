import os
from src.order_manager import OrderManager, split_csv_line


def join_csv(fields):
    """Put fields back into a CSV line, quoting any that contain commas."""
    return ",".join(
        '"' + f.replace('"', '""') + '"' if ("," in f or '"' in f) else f
        for f in fields)


# Take the real header and one real good row from the dataset.
with open("data/Amazon Sale Report.csv", encoding="utf-8") as f:
    header = f.readline().rstrip("\r\n")
    good = f.readline().rstrip("\r\n")

names = [h.strip() for h in split_csv_line(header)]
fields = split_csv_line(good)


def broken(column, value):
    copy = list(fields)
    copy[names.index(column)] = value
    return join_csv(copy)


rows = [
    good,                         # valid                    -> loaded
    broken("Date", "13-45-22"),   # impossible date          -> skipped
    broken("Date", "not a date"), # text instead of a date   -> skipped
    broken("Qty", "abc"),         # Qty is not a number      -> skipped
    broken("Qty", ""),            # Qty missing              -> skipped
    broken("Amount", "xyz"),      # Amount is not a number   -> skipped
    broken("Amount", ""),         # Amount missing           -> kept, repaired to 0.0
    "a,b,c",                      # too few columns          -> skipped
]

test_path = "data/_broken_test.csv"
with open(test_path, "w", encoding="utf-8") as f:
    f.write(header + "\n" + "\n".join(rows) + "\n")

m = OrderManager()
m.load_orders(test_path)
print(f"loaded={len(m)} (expect 2) | skipped={len(m.skipped)} (expect 6) | repaired={len(m.warnings)} (expect 1)")
for line_no, reason in m.skipped:
    print(f"  skipped line {line_no}: {reason}")
for line_no, reason in m.warnings:
    print(f"  repaired line {line_no}: {reason}")
os.remove(test_path)

# A missing file must give a clear error, not a crash.
try:
    OrderManager().load_orders("data/does_not_exist.csv")
except FileNotFoundError as e:
    print("Missing file handled:", e)