with sales as (
    select * from {{ ref('stg_sales') }}
),
calculated as (
    select
        sale_date,
        store_id,
        product_id,
        units_sold,
        price,
        discount_percentage,
        -- Calculate Revenue
        (units_sold * price * (1 - (discount_percentage / 100.0))) as revenue,
        
        inventory_level,
        demand_forecast,
        -- Calculate Stock Gap
        (inventory_level - demand_forecast) as stock_gap,
        
        -- Calculate Fulfillment Rate (capping at 1.0)
        case 
            when demand_forecast = 0 then 0 
            else least((units_sold * 1.0) / demand_forecast, 1.0) 
        end as fulfillment_rate,
        
        weather_condition,
        holiday_promotion,
        seasonality
    from sales
)
select * from calculated
