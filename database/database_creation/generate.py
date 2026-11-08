"""
generate.py — Step 1.8: generate synthetic business records.

Builds every row in memory and returns them as {table_name: [row tuples]}.
Touches no database; load.py does the inserting.

All randomness comes from ONE seeded generator (rng), so the same SEED
always produces exactly the same data across all tables.
"""

import random
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Settings — change these to resize the database
# ---------------------------------------------------------------------------
SEED = 42
N_CUSTOMERS = 500
N_ORDERS = 3000
START = date(2024, 1, 1)
END = date(2025, 12, 31)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
CATEGORIES = {
    # name: (type, [(product, min_price, max_price), ...])
    "Electronics": ("durable", [
        ("Wireless Earbuds", 1500, 6000), ("Smartphone", 12000, 60000),
        ("Bluetooth Speaker", 1200, 8000), ("Smartwatch", 2500, 20000),
        ("Power Bank", 800, 3000), ("Laptop", 35000, 110000),
        ("USB-C Charger", 500, 2500), ("Tablet", 15000, 55000),
    ]),
    "Fashion": ("apparel", [
        ("Cotton T-Shirt", 300, 1200), ("Denim Jeans", 900, 3500),
        ("Running Shoes", 1500, 7000), ("Kurta", 600, 2500),
        ("Leather Wallet", 400, 2000), ("Sunglasses", 500, 4000),
        ("Hoodie", 800, 3000),
    ]),
    "Home & Kitchen": ("durable", [
        ("Non-stick Pan", 600, 2500), ("Mixer Grinder", 2000, 7000),
        ("Bedsheet Set", 700, 3000), ("Table Lamp", 500, 2500),
        ("Water Bottle", 200, 900), ("Pressure Cooker", 1200, 4000),
        ("Storage Containers", 300, 1500),
    ]),
    "Groceries": ("consumable", [
        ("Basmati Rice 5kg", 450, 900), ("Olive Oil 1L", 600, 1200),
        ("Green Tea 100 bags", 250, 600), ("Almonds 500g", 400, 800),
        ("Instant Coffee 200g", 350, 750), ("Honey 500g", 250, 550),
    ]),
    "Beauty & Personal Care": ("consumable", [
        ("Face Wash", 150, 600), ("Shampoo 650ml", 300, 800),
        ("Sunscreen SPF50", 300, 900), ("Electric Trimmer", 1000, 3500),
        ("Perfume", 800, 4000), ("Moisturiser", 250, 900),
    ]),
    "Books": ("media", [
        ("Python Programming Guide", 400, 1200), ("Fiction Novel", 250, 700),
        ("Cookbook", 350, 1000), ("Self-help Book", 250, 600),
        ("Children's Storybook", 150, 500),
    ]),
    "Sports & Fitness": ("durable", [
        ("Yoga Mat", 400, 1800), ("Dumbbell Set", 1200, 5000),
        ("Cricket Bat", 1000, 6000), ("Football", 400, 1500),
        ("Resistance Bands", 300, 1200), ("Cycling Helmet", 800, 3000),
    ]),
    "Toys": ("durable", [
        ("Building Blocks Set", 600, 3000), ("Remote Control Car", 800, 3500),
        ("Board Game", 500, 2500), ("Puzzle 1000pc", 400, 1200),
        ("Soft Toy", 300, 1200),
    ]),
}

WAREHOUSES = [
    ("North Hub", "Delhi"), ("West Hub", "Mumbai"), ("South Hub", "Bengaluru"),
    ("East Hub", "Kolkata"), ("Central Hub", "Hyderabad"),
]

CITIES = ["Delhi", "Mumbai", "Bengaluru", "Kolkata", "Hyderabad", "Chennai",
          "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Kochi", "Chandigarh",
          "Indore", "Bhopal", "Guwahati"]

FIRST = ["Aarav", "Vivaan", "Aditya", "Ananya", "Diya", "Ishaan", "Kavya",
         "Rohan", "Saanvi", "Arjun", "Meera", "Kabir", "Priya", "Rahul",
         "Sneha", "Vikram", "Neha", "Karan", "Pooja", "Siddharth", "Fatima",
         "Imran", "Sara", "John", "Maria", "Tenzin", "Harpreet", "Lakshmi"]
LAST = ["Sharma", "Verma", "Iyer", "Reddy", "Nair", "Gupta", "Singh",
        "Patel", "Das", "Khan", "Menon", "Joshi", "Rao", "Kapoor", "Bose",
        "Fernandes", "Mehta", "Chatterjee", "Pillai", "Banerjee"]

PAYMENT_METHODS = ["upi", "credit_card", "debit_card", "net_banking", "cod", "wallet"]
PAYMENT_WEIGHTS = [40, 20, 15, 8, 12, 5]
CARRIERS = ["BlueDart", "Delhivery", "Ekart", "DTDC", "India Post"]
RETURN_REASONS = ["damaged", "wrong_item", "size_issue", "not_as_described",
                  "changed_mind", "defective"]

ORDER_STATUSES = ["delivered", "shipped", "processing", "pending", "cancelled"]
STATUS_WEIGHTS = [65, 10, 8, 5, 12]


# ---------------------------------------------------------------------------
# Generators — one per group of tables. Each takes the shared rng.
# ---------------------------------------------------------------------------
def rand_date(rng: random.Random, lo: date, hi: date) -> date:
    return lo + timedelta(days=rng.randint(0, (hi - lo).days))


def gen_catalog(rng):
    """Build the product catalogue: categories + products.

    Returns:
        categories: [(category_id, category_name, category_type), ...]
        products:   [(product_id, category_id, product_name, price, cost_price), ...]
    """
    categories, products = [], []
    pid = 0                                   # running product_id counter: 1, 2, 3, ...

    # enumerate(..., start=1) gives the 8 categories IDs 1 to 8
    for cid, (cname, (ctype, items)) in enumerate(CATEGORIES.items(), start=1):
        categories.append((cid, cname, ctype))

        # each product stores its category's ID -> the products.category_id FK
        for pname, lo, hi in items:
            pid += 1

            # random price inside this product's range, rounded to the nearest 10,
            # then minus 1 so it looks like a shop price: 2513.4 -> 2510 -> 2509.0
            price = round(rng.uniform(lo, hi), -1) - 1

            # cost is 55–80% of the price, so every product has a positive margin
            cost = round(price * rng.uniform(0.55, 0.80), 2)

            products.append((pid, cid, pname, price, cost))

    return categories, products


def gen_stock(rng, products):
    """Build warehouses + inventory (how much of each product sits where).

    Returns:
        warehouses: [(warehouse_id, warehouse_name, city), ...]
        inventory:  [(inventory_id, product_id, warehouse_id, stock_quantity, reorder_level), ...]
    """
    # the 5 fixed warehouses, given IDs 1 to 5
    warehouses = [(wid, name, city) for wid, (name, city) in enumerate(WAREHOUSES, start=1)]

    inventory = []
    inv_id = 0                                # running inventory_id counter

    for p in products:                        # p = (product_id, category_id, name, price, cost)
        # stock this product in 2–4 DIFFERENT warehouses (sample never repeats),
        # so no (product, warehouse) pair appears twice -> matches the UNIQUE rule
        for wid in rng.sample(range(1, len(WAREHOUSES) + 1), k=rng.randint(2, 4)):
            inv_id += 1

            # the stock level at which this warehouse should reorder
            reorder = rng.randint(20, 60)

            # 15% of rows: stock BELOW the reorder level (low-stock questions have answers)
            # 85% of rows: healthy stock between the reorder level and 500
            stock = (rng.randint(0, reorder - 1) if rng.random() < 0.15
                     else rng.randint(reorder, 500))

            inventory.append((inv_id, p[0], wid, stock, reorder))   # p[0] = product_id

    return warehouses, inventory


def gen_customers(rng):
    """Build N_CUSTOMERS customers.

    Returns:
        customers: [(customer_id, name, email, city, registration_date), ...]
    """
    customers = []

    for cid in range(1, N_CUSTOMERS + 1):    # customer IDs 1 to N_CUSTOMERS
        # random name from the two lists (names CAN repeat, like real life)
        first, last = rng.choice(FIRST), rng.choice(LAST)

        
        reg = rand_date(rng, date(2023, 1, 1), date(2025, 9, 30))

        customers.append((
            cid,
            f"{first} {last}",
            f"{first.lower()}.{last.lower()}{cid}@example.com",# the ID inside the email keeps every email unique even when names repeat,
            rng.choice(CITIES),
            reg.isoformat(),                  # date -> "2024-03-15" text for SQLite
        ))

    return customers


def gen_orders(rng, customers, products):
    """orders + order_items + payments + shipments + returns.

    Generated together because they depend on each other: an order's
    status decides whether it gets a shipment, which decides whether it
    can have a return; payment amount is the sum of its items.
    """
    orders, items, payments, shipments, returns = [], [], [], [], []

    # quick lookups built from the earlier tables
    price_of = {p[0]: p[3] for p in products}                      # product_id -> price
    catalogue = [(p[0], p[3]) for p in products]                   # [(product_id, price), ...]
    cust = [(c[0], date.fromisoformat(c[4])) for c in customers]   # [(customer_id, reg_date), ...]

    # running ID counters for each child table
    item_id = pay_id = ship_id = ret_id = 0

    # one weight per customer from a Pareto distribution: most weights are small,
    # a few are large -> a few customers place MANY orders, most place one or two
    cust_weights = [rng.paretovariate(1.5) for _ in cust]

    for oid in range(1, N_ORDERS + 1):        # order IDs 1 to N_ORDERS

        # ---- orders -----------------------------------------------------------
        # pick a customer, favouring the heavy buyers
        cid, reg = rng.choices(cust, weights=cust_weights)[0]

        # order date: not before the customer registered, and inside START..END
        odate = rand_date(rng, max(reg, START), END)

        # ~65% delivered, 12% cancelled, the rest shipped / processing / pending
        status = rng.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS)[0]
        orders.append((oid, cid, odate.isoformat(), status))

        # ---- order_items ------------------------------------------------------
        lines = []                            # (product_id, qty) for this order, reused below

        # how many lines: 1 (50%), 2 (30%), 3 (15%), 4 (5%)
        n_lines = rng.choices([1, 2, 3, 4], [50, 30, 15, 5])[0]

        # sample() picks DIFFERENT products, so no product repeats inside one order
        for p, price in rng.sample(catalogue, k=n_lines):
            item_id += 1
            qty = rng.choices([1, 2, 3, 5], [70, 20, 7, 3])[0]   # mostly 1 unit
            items.append((item_id, oid, p, qty, price))         # unit_price = catalogue price
            lines.append((p, qty))

        # order total = sum of quantity x price over its lines
        total = round(sum(q * price_of[p] for p, q in lines), 2)

        # ---- payments ---------------------------------------------------------
        # one payment per order; amount ALWAYS equals the order total
        method = rng.choices(PAYMENT_METHODS, PAYMENT_WEIGHTS)[0]

        # payment status must make sense for the order status
        if status == "cancelled":
            pstatus = "failed" if rng.random() < 0.4 else "refunded"   # 40% failed, 60% refunded
        elif method == "cod" and status != "delivered":
            pstatus = "pending"               # cash on delivery: not paid until it arrives
        elif status == "pending":
            pstatus = "pending"
        else:
            pstatus = "completed"

        pay_id += 1
        payments.append((pay_id, oid, method, pstatus, total))

        # ---- shipments --------------------------------------------------------
        # only orders that have left the warehouse get a shipment row
        if status in ("shipped", "delivered"):
            ship_id += 1

            if status == "delivered":
                # arrived 2–9 days after the order was placed
                ddate = odate + timedelta(days=rng.randint(2, 9))
                shipments.append((ship_id, oid, rng.choice(CARRIERS), "delivered",
                                  ddate.isoformat()))

                # ---- returns ----------------------------------------------------
                # only delivered orders can be returned; ~8% of them are
                if rng.random() < 0.08:
                    # return one of THIS order's own items, never a random product
                    p, qty = rng.choice(lines)
                    ret_id += 1
                    returns.append((
                        ret_id, oid, p,
                        rng.randint(1, qty),          # can't return more than was bought
                        rng.choice(RETURN_REASONS),
                        # returned 1–15 days after delivery
                        (ddate + timedelta(days=rng.randint(1, 15))).isoformat(),
                    ))
            else:
                # shipped but not arrived: no delivery date yet (None -> NULL in SQL)
                shipments.append((ship_id, oid, rng.choice(CARRIERS), "in_transit", None))

    return orders, items, payments, shipments, returns


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def generate_all(seed: int = SEED) -> dict:
    """Return {table_name: [rows]} for all 10 tables."""
    rng = random.Random(seed)             # the ONE source of randomness
    categories, products = gen_catalog(rng)
    warehouses, inventory = gen_stock(rng, products)
    customers = gen_customers(rng)
    orders, items, payments, shipments, returns = gen_orders(rng, customers, products)
    return {
        "categories": categories, "products": products,
        "warehouses": warehouses, "inventory": inventory,
        "customers": customers, "orders": orders, "order_items": items,
        "payments": payments, "shipments": shipments, "returns": returns,
    }


if __name__ == "__main__":
    for table, rows in generate_all().items():
        print(f"{table:<12} {len(rows):>6} rows   e.g. {rows[0]}")