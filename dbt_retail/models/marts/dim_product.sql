with sales as (
    select * from {{ ref('stg_sales') }}
),
products as (
    select distinct
        product_id,
        category,
        price,
        competitor_pricing
    from sales
)
select * from products
