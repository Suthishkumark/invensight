with base as (
    select
        f.store_id,
        f.product_id,
        p.category,
        AVG(f.inventory_level)  as avg_inventory,
        AVG(f.units_sold)       as avg_units_sold,
        AVG(f.demand_forecast)  as avg_demand_forecast,
        AVG(f.fulfillment_rate) as avg_fulfillment,
        SUM(f.revenue)          as total_revenue,
        COUNT(*)                as records
    from {{ ref('fct_sales') }} f
    left join {{ ref('dim_product') }} p using (product_id)
    group by 1, 2, 3
),
with_days as (
    select
        *,
        case
            when (avg_units_sold / 30.0) <= 0 then null
            else ROUND(avg_inventory / (avg_units_sold / 30.0), 1)
        end as days_of_stock
    from base
),
with_alerts as (
    select
        *,
        case
            when days_of_stock is null  then 'UNKNOWN'
            when days_of_stock < 30     then 'UNDERSTOCK'
            when days_of_stock > 120    then 'OVERSTOCK'
            else                             'HEALTHY'
        end as alert_status,
        case
            when days_of_stock < 30 then ROUND(30 - days_of_stock, 1)
            else 0
        end as urgency_score
    from with_days
)
select * from with_alerts
order by urgency_score desc, days_of_stock asc nulls last
