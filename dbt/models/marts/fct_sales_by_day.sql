{{ config(materialized="table") }}

with sales_lines as (
  select * from {{ ref('int_sales_line_items') }}
)

select
  tenant_id,
  date(processed_at) as sales_date,
  currency,

  count(distinct order_id) as orders_count,
  sum(line_gross) as gross_sales,
  sum(line_refund_alloc) as refunds_allocated,
  sum(line_gross - line_refund_alloc) as net_sales

from sales_lines
where processed_at is not null
group by 1,2,3
