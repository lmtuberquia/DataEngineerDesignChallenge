{{ config(materialized="view") }}

with src as (
  select
    tenant_id,
    cast(order_id as string) as order_id,
    cast(product_id as string) as product_id,
    sku,
    cast(quantity as int64) as quantity,
    cast(price as numeric) as price,

    cast(updated_at as timestamp) as updated_at,

    -- Airbyte often lands JSON arrays as strings; keep as string in staging
    cast(discount_allocations as string) as discount_allocations,

    cast(ingested_at as timestamp) as ingested_at
  from {{ source('raw_shared', 'shopify_order_line_items') }}
)

select * from src
