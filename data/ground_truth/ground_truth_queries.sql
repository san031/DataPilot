-- Q01: Which five customers have placed the highest number of orders?
SELECT c.customer_id, c.name, COUNT(o.order_id) AS total_orders
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_orders DESC, c.customer_id
LIMIT 5;


-- Q02: How many customers are registered in each city?
SELECT city, COUNT(*) AS customer_count
FROM customers
GROUP BY city
ORDER BY customer_count DESC, city;


-- Q03: Which customers have never placed an order?
SELECT c.customer_id, c.name, c.city
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_id IS NULL
ORDER BY c.customer_id;


-- Q04: Which five products generated the highest paid sales revenue?
SELECT p.product_id, p.product_name,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS paid_sales_revenue
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
JOIN payments pay ON pay.order_id = oi.order_id
WHERE pay.payment_status = 'completed'
GROUP BY p.product_id, p.product_name
ORDER BY paid_sales_revenue DESC, p.product_id
LIMIT 5;


-- Q05: Which product categories generated the highest paid sales revenue?
SELECT c.category_id, c.category_name,
       ROUND(SUM(oi.quantity * oi.unit_price), 2) AS paid_sales_revenue
FROM categories c
JOIN products p ON p.category_id = c.category_id
JOIN order_items oi ON oi.product_id = p.product_id
JOIN payments pay ON pay.order_id = oi.order_id
WHERE pay.payment_status = 'completed'
GROUP BY c.category_id, c.category_name
ORDER BY paid_sales_revenue DESC, c.category_id;


-- Q06: What is the average listed product price in each category?
SELECT c.category_id, c.category_name,
       ROUND(AVG(p.price), 2) AS average_listed_price
FROM categories c
JOIN products p ON p.category_id = c.category_id
GROUP BY c.category_id, c.category_name
ORDER BY average_listed_price DESC, c.category_id;


-- Q07: Which five products generated the highest gross profit from completed payments?
SELECT p.product_id, p.product_name,
       ROUND(SUM(oi.quantity * (oi.unit_price - p.cost_price)), 2) AS gross_profit
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
JOIN payments pay ON pay.order_id = oi.order_id
WHERE pay.payment_status = 'completed'
GROUP BY p.product_id, p.product_name
ORDER BY gross_profit DESC, p.product_id
LIMIT 5;


-- Q08: How many orders were placed in each month?
SELECT strftime('%Y-%m', order_date) AS order_month,
       COUNT(*) AS order_count
FROM orders
GROUP BY strftime('%Y-%m', order_date)
ORDER BY order_month;


-- Q09: What is the total value of completed payments?
SELECT ROUND(COALESCE(SUM(amount), 0), 2) AS total_completed_payment_value
FROM payments
WHERE payment_status = 'completed';


-- Q10: How many orders are there in each order status?
SELECT order_status, COUNT(*) AS order_count
FROM orders
GROUP BY order_status
ORDER BY order_count DESC, order_status;


-- Q11: Which payment methods are used most frequently, and how many payments use each method?
SELECT payment_method, COUNT(*) AS payment_count
FROM payments
GROUP BY payment_method
ORDER BY payment_count DESC, payment_method;


-- Q12: Which products are below their reorder level at any warehouse? Show the warehouse and stock details.
SELECT p.product_id, p.product_name, w.warehouse_name,
       i.stock_quantity, i.reorder_level
FROM inventory i
JOIN products p ON p.product_id = i.product_id
JOIN warehouses w ON w.warehouse_id = i.warehouse_id
WHERE i.stock_quantity < i.reorder_level
ORDER BY (i.reorder_level - i.stock_quantity) DESC, p.product_id, w.warehouse_id;


-- Q13: Which warehouse holds the greatest total number of inventory units? Show totals for all warehouses.
SELECT w.warehouse_id, w.warehouse_name, w.city,
       SUM(i.stock_quantity) AS total_stock_units
FROM warehouses w
JOIN inventory i ON i.warehouse_id = w.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, w.city
ORDER BY total_stock_units DESC, w.warehouse_id;


-- Q14: What is the total stock quantity of each product across all warehouses?
SELECT p.product_id, p.product_name,
       SUM(i.stock_quantity) AS total_stock_units
FROM products p
JOIN inventory i ON i.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY total_stock_units DESC, p.product_id;


-- Q15: How many additional units should be ordered to bring every below-reorder inventory record up to its reorder level? Show the requirement by product.
SELECT p.product_id, p.product_name,
       SUM(CASE WHEN i.stock_quantity < i.reorder_level
                THEN i.reorder_level - i.stock_quantity ELSE 0 END) AS units_to_restock
FROM products p
JOIN inventory i ON i.product_id = p.product_id
GROUP BY p.product_id, p.product_name
HAVING units_to_restock > 0
ORDER BY units_to_restock DESC, p.product_id;


-- Q16: How many shipments are currently in transit?
SELECT COUNT(*) AS in_transit_shipments
FROM shipments
WHERE shipping_status = 'in_transit';


-- Q17: Which shipping carriers have handled the most shipments?
SELECT carrier, COUNT(*) AS shipment_count
FROM shipments
GROUP BY carrier
ORDER BY shipment_count DESC, carrier;


-- Q18: What are the most common reasons for product returns?
SELECT return_reason, COUNT(*) AS return_count,
       SUM(quantity) AS units_returned
FROM returns
GROUP BY return_reason
ORDER BY return_count DESC, return_reason;


-- Q19: Which five customers have the highest total value of completed purchases?
SELECT c.customer_id, c.name,
       ROUND(SUM(pay.amount), 2) AS completed_purchase_value
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN payments pay ON pay.order_id = o.order_id
WHERE pay.payment_status = 'completed'
GROUP BY c.customer_id, c.name
ORDER BY completed_purchase_value DESC, c.customer_id
LIMIT 5;


-- Q20: Among products with at least one warehouse below its reorder level, which five have the highest paid sales revenue? Include their total stock and number of low-stock warehouse records.
WITH product_sales AS (
    SELECT oi.product_id,
           SUM(oi.quantity * oi.unit_price) AS paid_sales_revenue
    FROM order_items oi
    JOIN payments pay ON pay.order_id = oi.order_id
    WHERE pay.payment_status = 'completed'
    GROUP BY oi.product_id
),
product_inventory AS (
    SELECT product_id,
           SUM(stock_quantity) AS total_stock_units,
           SUM(CASE WHEN stock_quantity < reorder_level THEN 1 ELSE 0 END) AS low_stock_warehouse_records
    FROM inventory
    GROUP BY product_id
)
SELECT p.product_id, p.product_name,
       ROUND(COALESCE(ps.paid_sales_revenue, 0), 2) AS paid_sales_revenue,
       pi.total_stock_units, pi.low_stock_warehouse_records
FROM products p
JOIN product_inventory pi ON pi.product_id = p.product_id
LEFT JOIN product_sales ps ON ps.product_id = p.product_id
WHERE pi.low_stock_warehouse_records > 0
ORDER BY paid_sales_revenue DESC, p.product_id
LIMIT 5;
