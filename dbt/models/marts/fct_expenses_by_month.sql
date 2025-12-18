{{ config(materialized="table") }}

with expenses as (
  select * from {{ ref('int_expenses_normalized') }}
)

select
  tenant_id,
  date_trunc(txn_date, month) as expense_month,
  account_type,
  account_name,

  sum(amount) as total_expenses,
  count(*) as expense_txn_count
from expenses
group by 1,2,3,4
