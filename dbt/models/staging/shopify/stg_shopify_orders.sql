{{ config(materialized="view") }}

with src as (
  select
    tenant_id,
    cast(id as string) as order_id,

    -- timestamps
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at,
    cast(processed_at as timestamp) as processed_at,

    -- measures
    cast(total_discounts as numeric) as total_discounts,
    cast(total_tax as numeric) as total_tax,

    currency,
    financial_status,
    source_name,

    -- meta (if present)
    cast(ingested_at as timestamp) as ingested_at
  from {{ source('raw_shared', 'shopify_orders') }}
)

select * from src
