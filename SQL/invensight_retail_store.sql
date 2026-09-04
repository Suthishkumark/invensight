-- ============================================================
--   InvenSight: Smart Stock Analytics & Demand Prediction
--   SQL Queries for retail_store.csv dataset
--   Table: retail_store
--   Columns: Date, Store ID, Product ID, Category, Region,
--            Inventory Level, Units Sold, Units Ordered,
--            Demand Forecast, Price, Discount,
--            Weather Condition, Holiday/Promotion,
--            Competitor Pricing, Seasonality
-- ============================================================

USE invensight;

-- ============================================================
-- QUERY 1: Verify Data Loaded Correctly (Run this FIRST!)
-- ============================================================
SELECT
    COUNT(*)                        AS total_rows,
    COUNT(DISTINCT `Store ID`)      AS total_stores,
    COUNT(DISTINCT `Product ID`)    AS total_products,
    COUNT(DISTINCT `Category`)      AS total_categories,
    COUNT(DISTINCT `Region`)        AS total_regions,
    MIN(`Date`)                     AS date_from,
    MAX(`Date`)                     AS date_to
FROM retail_store;


-- ============================================================
-- QUERY 2: Total Sales Per Store
-- ============================================================
SELECT
    `Store ID`,
    COUNT(*)                            AS total_records,
    SUM(`Units Sold`)                   AS total_units_sold,
    ROUND(SUM(`Units Sold` * `Price`
        * (1 - `Discount` / 100)), 2)   AS total_revenue,
    ROUND(AVG(`Units Sold`), 2)         AS avg_daily_units,
    ROUND(AVG(`Inventory Level`), 2)    AS avg_inventory
FROM retail_store
GROUP BY `Store ID`
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 3: Total Sales Per Category
-- ============================================================
SELECT
    `Category`,
    SUM(`Units Sold`)                   AS total_units_sold,
    ROUND(SUM(`Units Sold` * `Price`
        * (1 - `Discount` / 100)), 2)   AS total_revenue,
    ROUND(AVG(`Units Sold`), 2)         AS avg_units_per_day,
    ROUND(AVG(`Inventory Level`), 2)    AS avg_inventory,
    ROUND(AVG(`Demand Forecast`), 2)    AS avg_demand_forecast
FROM retail_store
GROUP BY `Category`
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 4: Sales by Region
-- ============================================================
SELECT
    `Region`,
    COUNT(DISTINCT `Store ID`)          AS stores_in_region,
    SUM(`Units Sold`)                   AS total_units_sold,
    ROUND(SUM(`Units Sold` * `Price`
        * (1 - `Discount` / 100)), 2)   AS total_revenue,
    ROUND(AVG(`Inventory Level`), 2)    AS avg_inventory
FROM retail_store
GROUP BY `Region`
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 5: Holiday vs Non-Holiday Sales
-- ============================================================
SELECT
    CASE WHEN `Holiday/Promotion` = 1
         THEN 'Holiday/Promo'
         ELSE 'Regular Day'
    END                                 AS day_type,
    COUNT(*)                            AS total_records,
    ROUND(AVG(`Units Sold`), 2)         AS avg_units_sold,
    ROUND(AVG(`Demand Forecast`), 2)    AS avg_demand,
    ROUND(SUM(`Units Sold` * `Price`
        * (1 - `Discount` / 100)), 2)   AS total_revenue
FROM retail_store
GROUP BY `Holiday/Promotion`;


-- ============================================================
-- QUERY 6: Weather Impact on Sales
-- ============================================================
SELECT
    `Weather Condition`,
    COUNT(*)                            AS total_records,
    ROUND(AVG(`Units Sold`), 2)         AS avg_units_sold,
    ROUND(AVG(`Inventory Level`), 2)    AS avg_inventory,
    ROUND(AVG(`Demand Forecast`), 2)    AS avg_demand_forecast
FROM retail_store
GROUP BY `Weather Condition`
ORDER BY avg_units_sold DESC;


-- ============================================================
-- QUERY 7: Seasonality Impact on Sales
-- ============================================================
SELECT
    `Seasonality`,
    COUNT(*)                            AS total_records,
    SUM(`Units Sold`)                   AS total_units_sold,
    ROUND(AVG(`Units Sold`), 2)         AS avg_units_sold,
    ROUND(SUM(`Units Sold` * `Price`
        * (1 - `Discount` / 100)), 2)   AS total_revenue
FROM retail_store
GROUP BY `Seasonality`
ORDER BY total_revenue DESC;


-- ============================================================
-- QUERY 8: Understock Alert
-- Products where Inventory Level < Demand Forecast
-- ============================================================
SELECT
    `Store ID`,
    `Product ID`,
    `Category`,
    `Region`,
    ROUND(AVG(`Inventory Level`), 2)    AS avg_inventory,
    ROUND(AVG(`Demand Forecast`), 2)    AS avg_demand,
    ROUND(AVG(`Units Sold`), 2)         AS avg_units_sold,
    ROUND(AVG(`Inventory Level`) -
          AVG(`Demand Forecast`), 2)    AS stock_gap,
    'UNDERSTOCK'                        AS alert_status
FROM retail_store
GROUP BY `Store ID`, `Product ID`, `Category`, `Region`
HAVING avg_inventory < avg_demand
ORDER BY stock_gap ASC
LIMIT 20;


-- ============================================================
-- QUERY 9: Overstock Alert
-- Products where Inventory Level >> Demand Forecast
-- ============================================================
SELECT
    `Store ID`,
    `Product ID`,
    `Category`,
    `Region`,
    ROUND(AVG(`Inventory Level`), 2)    AS avg_inventory,
    ROUND(AVG(`Demand Forecast`), 2)    AS avg_demand,
    ROUND(AVG(`Units Sold`), 2)         AS avg_units_sold,
    ROUND(AVG(`Inventory Level`) -
          AVG(`Demand Forecast`), 2)    AS stock_gap,
    ROUND(AVG(`Discount`), 2)           AS avg_discount,
    'OVERSTOCK'                         AS alert_status
FROM retail_store
GROUP BY `Store ID`, `Product ID`, `Category`, `Region`
HAVING avg_inventory > avg_demand * 2
ORDER BY stock_gap DESC
LIMIT 20;


-- ============================================================
-- QUERY 10: Final Master Table — Export this for Power BI!
-- ============================================================
SELECT
    `Date`,
    `Store ID`,
    `Product ID`,
    `Category`,
    `Region`,
    `Inventory Level`,
    `Units Sold`,
    `Units Ordered`,
    `Demand Forecast`,
    `Price`,
    `Discount`,
    `Weather Condition`,
    `Holiday/Promotion`,
    `Competitor Pricing`,
    `Seasonality`,
    ROUND(`Units Sold` * `Price`
        * (1 - `Discount` / 100), 2)   AS Revenue,
    ROUND(`Inventory Level` -
          `Demand Forecast`, 2)         AS Stock_Gap,
    CASE
        WHEN `Inventory Level` < `Demand Forecast`
             THEN 'UNDERSTOCK'
        WHEN `Inventory Level` > `Demand Forecast` * 2
             THEN 'OVERSTOCK'
        ELSE 'HEALTHY'
    END                                 AS Alert_Status
FROM retail_store
ORDER BY `Store ID`, `Product ID`, `Date`;
