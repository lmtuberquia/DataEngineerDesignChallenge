{{ config(materialized="view") }}

with src as (
  select
    tenant_id,
    cast(txn_id as string) as expense_id,
    cast(txn_date as date) as txn_date,

    cast(vendor_id as string) as vendor_id,
    account_name,
    account_type,

    cast(amount as numeric) as amount,
    class,
    memo,

    cast(updated_at as timestamp) as updated_at,
    cast(ingested_at as timestamp) as ingested_at
  from {{ source('raw_shared', 'qb_expenses') }}
)

select * from src
