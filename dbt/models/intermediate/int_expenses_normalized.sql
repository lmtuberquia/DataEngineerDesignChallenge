{{ config(materialized="table") }}

with e as (
  select * from {{ ref('stg_qb_expenses') }}
)

select
  tenant_id,
  expense_id,
  txn_date,
  vendor_id,
  account_name,
  account_type,
  amount,
  class,
  memo,
  updated_at
from e
