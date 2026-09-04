with daily as (
    select
        sale_date,
        seasonality,
        weather_condition,
        holiday_promotion,
        SUM(units_sold)       as actual_units,
        SUM(demand_forecast)  as forecasted_units,
        AVG(fulfillment_rate) as avg_fulfillment,
        COUNT(DISTINCT store_id || product_id) as product_store_count
    from {{ ref('fct_sales') }}
    group by 1, 2, 3, 4
),

seasonal_summary as (
    select
        seasonality,
        AVG(actual_units)      as avg_actual_units,
        AVG(forecasted_units)  as avg_forecasted_units,
        AVG(avg_fulfillment)   as avg_fulfillment
    from daily
    group by 1
),

weather_summary as (
    select
        weather_condition,
        AVG(actual_units)      as avg_actual_units,
        AVG(forecasted_units)  as avg_forecasted_units,
        AVG(avg_fulfillment)   as avg_fulfillment
    from daily
    group by 1
),

holiday_summary as (
    select
        holiday_promotion,
        AVG(actual_units)      as avg_actual_units,
        AVG(forecasted_units)  as avg_forecasted_units,
        AVG(avg_fulfillment)   as avg_fulfillment,
        COUNT(*) as days_count
    from daily
    group by 1
)

-- Main output: daily trend for actual vs forecast chart
select
    sale_date,
    seasonality,
    weather_condition,
    holiday_promotion,
    actual_units,
    forecasted_units,
    ROUND(actual_units - forecasted_units, 0) as forecast_error,
    avg_fulfillment
from daily
order by sale_date
