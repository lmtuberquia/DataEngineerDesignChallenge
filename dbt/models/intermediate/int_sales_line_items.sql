{{ config(materialized="table") }}

with orders as (
  select * from {{ ref('stg_shopify_orders') }}
),
lines as (
  select * from {{ ref('stg_shopify_order_line_items') }}
),
refunds as (
  select
    tenant_id,
    order_id,
    sum(amount) as refunded_amount
  from {{ ref('stg_shopify_refunds') }}
  group by 1,2
),

-- Order subtotal at line level (before refund allocation)
order_line_totals as (
  select
    tenant_id,
    order_id,
    sum(price * quantity) as order_lines_gross
  from lines
  group by 1,2
),

joined as (
  select
    l.tenant_id,
    l.order_id,
    l.product_id,
    l.sku,
    l.quantity,
    l.price,
    (l.price * l.quantity) as line_gross,

    o.created_at,
    o.processed_at,
    o.currency,
    o.financial_status,
    o.total_discounts,
    o.total_tax,

    coalesce(r.refunded_amount, 0) as refunded_amount,
    coalesce(olt.order_lines_gross, 0) as order_lines_gross
  from lines l
  join orders o
    on o.tenant_id = l.tenant_id
   and o.order_id = l.order_id
  left join refunds r
    on r.tenant_id = l.tenant_id
   and r.order_id = l.order_id
  left join order_line_totals olt
    on olt.tenant_id = l.tenant_id
   and olt.order_id = l.order_id
),

final as (
  select
    tenant_id,
    order_id,
    product_id,
    sku,
    created_at,
    processed_at,
    currency,
    financial_status,

    quantity,
    price,
    line_gross,

    -- Allocate order-level refund proportionally by line_gross
    case
      when order_lines_gross = 0 then 0
      else (line_gross / order_lines_gross) * refunded_amount
    end as line_refund_alloc,

    -- Simple approach: do not allocate discounts/tax to line items here (can be added later)
    total_discounts as order_total_discounts,
    total_tax as order_total_tax
  from joined
)

select * from final
