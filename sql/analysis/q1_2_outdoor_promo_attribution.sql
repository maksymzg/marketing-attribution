-- =========================================================================
-- Q1.2: Outdoor revenue attribution via WAW20 promo code
-- =========================================================================
-- Question: Q1.1 ranked outdoor lowest (ROAS 2.43), but acquisition_channel
--           attribution underestimates outdoor's true impact. WAW20 promo code
--           is our proxy for "billboard-influenced" orders.
--
-- Approach:
--   1. Count orders with promo_code = 'WAW20'
--   2. Sum their revenue
--   3. Compare to outdoor spend (240k PLN)
--   4. Compute "true" outdoor ROAS including WAW20 from non-outdoor customers
-- =========================================================================
-- Q1.2: WAW20 impact within outdoor channel
WITH outdoor_orders AS (
    SELECT 
        o.id,
        o.total_amount,
        o.promo_code,
        CASE 
            WHEN o.promo_code = 'WAW20' THEN 'with_waw20'
            ELSE 'no_promo'
        END AS promo_usage
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    WHERE c.acquisition_channel = 'outdoor'
)
SELECT 
    promo_usage,
    COUNT(*) AS num_orders,
    ROUND(SUM(total_amount)::numeric, 2) AS revenue_pln,
    ROUND(AVG(total_amount)::numeric, 2) AS avg_order_value,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER ()::numeric, 1) AS pct_of_outdoor_orders,
    ROUND(100.0 * SUM(total_amount) / SUM(SUM(total_amount)) OVER ()::numeric, 1) AS pct_of_outdoor_revenue
FROM outdoor_orders
GROUP BY promo_usage
ORDER BY revenue_pln DESC;