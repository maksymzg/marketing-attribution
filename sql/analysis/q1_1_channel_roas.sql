-- =========================================================================
-- Q1.1: Channel-level revenue & ROAS comparison
-- =========================================================================
-- Question: Which marketing channel has the highest ROAS?
--           Is outdoor (240k PLN budget) actually profitable?
--
-- Approach:
--   1. Calculate revenue per acquisition_channel (from orders + customers)
--   2. Calculate spend per channel (from marketing_spend)
--   3. Compute ROAS = revenue / spend
--   4. Rank channels by ROAS
-- =========================================================================
WITH 
revenue_per_channel AS (
    SELECT 
        c.acquisition_channel AS channel,
        COUNT(DISTINCT o.id) AS num_orders,
        SUM(o.total_amount) AS total_revenue_pln
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    GROUP BY c.acquisition_channel
),
spend_per_channel AS (
    SELECT 
        channel,
        SUM(spend_pln) AS total_spend_pln
    FROM marketing_spend
    GROUP BY channel
)
SELECT 
    r.channel,
    r.num_orders,
    ROUND(r.total_revenue_pln::numeric, 2) AS revenue_pln,
    ROUND(s.total_spend_pln::numeric, 2) AS spend_pln,
    ROUND((r.total_revenue_pln / NULLIF(s.total_spend_pln, 0))::numeric, 2) AS roas,
    ROUND(((r.total_revenue_pln - s.total_spend_pln) / NULLIF(s.total_spend_pln, 0) * 100)::numeric, 1) AS profit_margin_pct
FROM revenue_per_channel r
LEFT JOIN spend_per_channel s ON r.channel = s.channel
ORDER BY roas DESC;