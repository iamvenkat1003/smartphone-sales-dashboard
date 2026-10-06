-- Smartphone Sales Dashboard: Learning and Verification Queries
--
-- SQLite stores dates as text in this project, using ISO-style YYYY-MM-DD
-- values. That format allows strftime() to group purchases by month.
--
-- Important revenue assumption:
-- sale_price is the price for one unit, so revenue is sale_price * quantity.


-- 1. Overall KPI summary
-- SUM adds quantities or monetary values across all purchase rows.
-- COUNT(DISTINCT user_id) counts each purchasing customer only once.
-- Average selling price divides total revenue by total units sold, so a
-- multi-unit purchase contributes the correct weight to the average.
SELECT
    COALESCE(SUM(quantity), 0) AS total_units_sold,
    ROUND(COALESCE(SUM(sale_price * quantity), 0), 2) AS total_revenue,
    COUNT(DISTINCT user_id) AS total_unique_customers,
    ROUND(
        COALESCE(
            SUM(sale_price * quantity) / NULLIF(SUM(quantity), 0),
            0
        ),
        2
    ) AS average_sale_price
FROM purchase;


-- 2. Top-selling phones by units sold
-- JOIN connects each purchase to its phone and manufacturer.
-- GROUP BY creates one result row per phone configuration.
-- SUM(quantity), rather than COUNT(*), handles purchases containing two units.
SELECT
    ph.phone_id,
    m.name AS manufacturer,
    ph.model_name,
    ph.storage_gb,
    SUM(p.quantity) AS units_sold
FROM purchase AS p
JOIN phone AS ph
    ON ph.phone_id = p.phone_id
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
GROUP BY
    ph.phone_id,
    m.name,
    ph.model_name,
    ph.storage_gb
ORDER BY units_sold DESC, manufacturer, ph.model_name;


-- 3. Top phones by revenue
-- Multiplying sale_price by quantity includes every unit in the revenue total.
SELECT
    ph.phone_id,
    m.name AS manufacturer,
    ph.model_name,
    ROUND(SUM(p.sale_price * p.quantity), 2) AS revenue
FROM purchase AS p
JOIN phone AS ph
    ON ph.phone_id = p.phone_id
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
GROUP BY
    ph.phone_id,
    m.name,
    ph.model_name
ORDER BY revenue DESC, manufacturer, ph.model_name;


-- 4. Manufacturer performance
-- LEFT JOIN keeps a manufacturer in the report even if it has no phone sales.
-- COALESCE converts the resulting NULL totals to zero.
SELECT
    m.name AS manufacturer,
    COALESCE(SUM(p.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(p.sale_price * p.quantity), 0), 2) AS revenue
FROM manufacturer AS m
LEFT JOIN phone AS ph
    ON ph.manufacturer_id = m.manufacturer_id
LEFT JOIN purchase AS p
    ON p.phone_id = ph.phone_id
GROUP BY
    m.manufacturer_id,
    m.name
ORDER BY revenue DESC, manufacturer;


-- 5. Sales by phone
-- COUNT(p.purchase_id) counts transactions, while SUM(p.quantity) counts units.
-- LEFT JOIN includes phones with no purchases in the result.
SELECT
    ph.phone_id,
    ph.model_name AS model,
    m.name AS manufacturer,
    COUNT(p.purchase_id) AS purchase_transactions,
    COALESCE(SUM(p.quantity), 0) AS units_sold,
    ROUND(COALESCE(SUM(p.sale_price * p.quantity), 0), 2) AS revenue,
    ROUND(
        COALESCE(
            SUM(p.sale_price * p.quantity) / NULLIF(SUM(p.quantity), 0),
            0
        ),
        2
    ) AS average_sale_price
FROM phone AS ph
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
LEFT JOIN purchase AS p
    ON p.phone_id = ph.phone_id
GROUP BY
    ph.phone_id,
    ph.model_name,
    m.name
ORDER BY units_sold DESC, manufacturer, model;


-- 6. Promotion usage
-- purchase_promotion is the bridge between purchases and promotions.
-- LEFT JOIN keeps unused promotions visible with zero uses and zero discount.
SELECT
    pr.promo_code,
    pr.promo_name,
    COUNT(pp.purchase_promo_id) AS times_used,
    ROUND(COALESCE(SUM(pp.discount_amount), 0), 2)
        AS total_discount_amount_applied
FROM promotion AS pr
LEFT JOIN purchase_promotion AS pp
    ON pp.promotion_id = pr.promotion_id
GROUP BY
    pr.promotion_id,
    pr.promo_code,
    pr.promo_name
ORDER BY times_used DESC, pr.promo_code;


-- 7. Promotion performance
-- Each purchase_promotion row represents one promotion used on one purchase.
-- Joining from that bridge to purchase counts a purchase once for each promotion
-- intentionally. A purchase with two promotions contributes once to each of
-- those two promotion rows, but never twice within the same promotion group.
-- Do not add these promotion-level revenue rows together for overall revenue,
-- because a multi-promotion purchase would then be counted more than once.
SELECT
    pr.promo_code AS promotion,
    m.name || ' ' || ph.model_name AS associated_phone,
    COUNT(DISTINCT pp.purchase_id) AS purchases_using_promotion,
    COALESCE(SUM(p.quantity), 0) AS units_sold_on_those_purchases,
    ROUND(COALESCE(SUM(p.sale_price * p.quantity), 0), 2)
        AS associated_revenue,
    ROUND(COALESCE(SUM(pp.discount_amount), 0), 2)
        AS total_discount_amount
FROM promotion AS pr
JOIN phone AS ph
    ON ph.phone_id = pr.phone_id
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
LEFT JOIN purchase_promotion AS pp
    ON pp.promotion_id = pr.promotion_id
LEFT JOIN purchase AS p
    ON p.purchase_id = pp.purchase_id
GROUP BY
    pr.promotion_id,
    pr.promo_code,
    m.name,
    ph.model_name
ORDER BY associated_revenue DESC, promotion;


-- 8. Sales trend by month
-- strftime('%Y-%m', ...) extracts a sortable year-month value.
-- GROUP BY places all purchases from the same month into one result row.
SELECT
    strftime('%Y-%m', purchase_date) AS month,
    COUNT(*) AS purchase_transactions,
    SUM(quantity) AS units_sold,
    ROUND(SUM(sale_price * quantity), 2) AS revenue
FROM purchase
GROUP BY strftime('%Y-%m', purchase_date)
ORDER BY month;


-- 9. Customer purchase summary
-- LEFT JOIN keeps customers who have not purchased anything yet.
-- COUNT(DISTINCT ph.model_name) counts different phone models purchased.
SELECT
    u.user_id,
    u.first_name || ' ' || u.last_name AS customer_name,
    COUNT(p.purchase_id) AS purchase_transactions,
    COUNT(DISTINCT ph.model_name) AS distinct_phone_models_purchased,
    COALESCE(SUM(p.quantity), 0) AS total_units_purchased,
    ROUND(COALESCE(SUM(p.sale_price * p.quantity), 0), 2)
        AS total_amount_spent
FROM user AS u
LEFT JOIN purchase AS p
    ON p.user_id = u.user_id
LEFT JOIN phone AS ph
    ON ph.phone_id = p.phone_id
GROUP BY
    u.user_id,
    u.first_name,
    u.last_name
ORDER BY total_amount_spent DESC, customer_name;


-- 10. Purchases with no promotion
-- LEFT JOIN first keeps every purchase. The NULL filter then selects purchases
-- that have no matching row in purchase_promotion.
SELECT
    p.purchase_id,
    p.purchase_date,
    u.first_name || ' ' || u.last_name AS customer_name,
    m.name AS manufacturer,
    ph.model_name,
    p.quantity,
    p.sale_price,
    ROUND(p.sale_price * p.quantity, 2) AS revenue
FROM purchase AS p
JOIN user AS u
    ON u.user_id = p.user_id
JOIN phone AS ph
    ON ph.phone_id = p.phone_id
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
LEFT JOIN purchase_promotion AS pp
    ON pp.purchase_id = p.purchase_id
WHERE pp.purchase_promo_id IS NULL
ORDER BY p.purchase_date, p.purchase_id;


-- 11. Purchases using exactly two promotions
-- The CTE groups bridge rows by purchase and retains only groups with two rows.
-- Joining afterward avoids mixing the promotion-counting step with sales data.
WITH two_promotion_purchases AS (
    SELECT purchase_id
    FROM purchase_promotion
    GROUP BY purchase_id
    HAVING COUNT(*) = 2
)
SELECT
    p.purchase_id,
    p.purchase_date,
    u.first_name || ' ' || u.last_name AS customer_name,
    m.name AS manufacturer,
    ph.model_name,
    p.quantity,
    ROUND(p.sale_price * p.quantity, 2) AS revenue,
    GROUP_CONCAT(pr.promo_code, ', ') AS promotion_codes,
    ROUND(SUM(pp.discount_amount), 2) AS total_discount_amount
FROM two_promotion_purchases AS tpp
JOIN purchase AS p
    ON p.purchase_id = tpp.purchase_id
JOIN user AS u
    ON u.user_id = p.user_id
JOIN phone AS ph
    ON ph.phone_id = p.phone_id
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
JOIN purchase_promotion AS pp
    ON pp.purchase_id = p.purchase_id
JOIN promotion AS pr
    ON pr.promotion_id = pp.promotion_id
GROUP BY
    p.purchase_id,
    p.purchase_date,
    u.first_name,
    u.last_name,
    m.name,
    ph.model_name,
    p.quantity,
    p.sale_price
ORDER BY p.purchase_date, p.purchase_id;


-- 12. Phone comparison for selected phone IDs
-- Replace the VALUES below with the phone IDs you want to compare.
-- Sales and promotion uses are aggregated in separate CTEs before joining.
-- This prevents a purchase with two promotions from doubling its units/revenue.
WITH selected_phone_ids(phone_id) AS (
    VALUES (1), (2)
),
phone_sales AS (
    SELECT
        phone_id,
        SUM(quantity) AS units_sold,
        SUM(sale_price * quantity) AS revenue,
        SUM(sale_price * quantity) / NULLIF(SUM(quantity), 0)
            AS average_sale_price
    FROM purchase
    GROUP BY phone_id
),
phone_promotion_uses AS (
    SELECT
        p.phone_id,
        COUNT(pp.purchase_promo_id) AS promotion_uses
    FROM purchase AS p
    JOIN purchase_promotion AS pp
        ON pp.purchase_id = p.purchase_id
    GROUP BY p.phone_id
)
SELECT
    ph.phone_id,
    m.name AS manufacturer,
    ph.model_name AS model,
    ph.ram_gb AS ram,
    ph.storage_gb AS storage,
    ph.launch_price,
    COALESCE(ps.units_sold, 0) AS units_sold,
    ROUND(COALESCE(ps.revenue, 0), 2) AS revenue,
    ROUND(COALESCE(ps.average_sale_price, 0), 2) AS average_sale_price,
    COALESCE(ppu.promotion_uses, 0) AS number_of_promotion_uses
FROM selected_phone_ids AS selected
JOIN phone AS ph
    ON ph.phone_id = selected.phone_id
JOIN manufacturer AS m
    ON m.manufacturer_id = ph.manufacturer_id
LEFT JOIN phone_sales AS ps
    ON ps.phone_id = ph.phone_id
LEFT JOIN phone_promotion_uses AS ppu
    ON ppu.phone_id = ph.phone_id
ORDER BY manufacturer, model;
