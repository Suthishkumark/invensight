with source as (
    select * from raw.sales
),
renamed as (
    select
        CAST("Date" AS DATE) as sale_date,
        "Store ID" as store_id,
        "Product ID" as product_id,
        "Category" as category,
        "Region" as region,
        "Inventory Level" as inventory_level,
        "Units Sold" as units_sold,
        "Demand Forecast" as demand_forecast,
        "Price" as price,
        "Discount" as discount_percentage,
        "Weather Condition" as weather_condition,
        "Holiday/Promotion" as holiday_promotion,
        "Seasonality" as seasonality,
        "Competitor Pricing" as competitor_pricing
    from source
    -- Basic cleaning: removing negative values as seen in the original script
    where "Units Sold" >= 0 
      and "Demand Forecast" >= 0 
      and "Inventory Level" >= 0
)
select * from renamed
