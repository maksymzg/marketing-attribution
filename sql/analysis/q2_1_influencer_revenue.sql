-- =========================================================================
-- Q2.1: Influencer-specific revenue (step 1: revenue only, no ROAS yet)
-- =========================================================================
-- Question: Which of 3 influencers generates the most revenue?
--           (Step 1 — revenue only. Step 2 — add spend & compute ROAS.)
--
-- Approach:
--   1. Filter orders by influencer promo codes
--   2. Group by promo code
--   3. Count orders + sum revenue per influencer
-- =========================================================================

SELECT o.promo_code, COUNT(*) AS num_orders, ROUND(SUM(o.total_amount), 2) AS revenue_pln
FROM orders o
WHERE o.promo_code IN ('PAWEL10', 'ZOFIA10', 'JANKOWAL15')
GROUP BY o.promo_code
ORDER BY revenue_pln DESC;