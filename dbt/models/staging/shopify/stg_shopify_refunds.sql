{{ config(materialized="view") }}

with src as (
  select
    tenant_id,
    cast(refund_id as string) as refund_id,
    cast(order_id as string) as order_id,
    cast(created_at as timestamp) as created_at,
    cast(amount as numeric) as amount,
    cast(ingested_at as timestamp) as ingested_at
  from {{ source('raw_shared', 'shopify_refunds') }}
)

select * from src
