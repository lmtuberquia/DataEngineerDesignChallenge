# Sample Data (Provided by Client)

This folder is a placeholder to document the **shape** of the sample tables described in the prompt.
In a real implementation, these would be created by Airbyte in BigQuery (raw landing zone).

## Tables (Raw Layer)

All raw tables are expected to include:
- `tenant_id` (string) — required for multi-tenancy
- source fields (as shown below)
- optional ingestion metadata (e.g., `ingested_at`, `_airbyte_emitted_at`, `_airbyte_raw_id`, etc.)

### `raw_shared.shopify_orders`
Example columns:
- `tenant_id`
- `id`
- `created_at`
- `updated_at`
- `total_discounts`
- `total_tax`
- `currency`
- `financial_status`
- `processed_at`
- `source_name`

### `raw_shared.shopify_order_line_items`
Example columns:
- `tenant_id`
- `order_id`
- `product_id`
- `sku`
- `quantity`
- `price`
- `updated_at`
- `discount_allocations` (often JSON-as-string)

### `raw_shared.shopify_refunds`
Example columns:
- `tenant_id`
- `refund_id`
- `order_id`
- `created_at`
- `amount`

### `raw_shared.qb_expenses`
Example columns:
- `tenant_id`
- `txn_id`
- `txn_date`
- `vendor_id`
- `account_name`
- `account_type`
- `amount`
- `class`
- `memo`
- `updated_at`

## Modeling Notes
The dbt models in `dbt/models/` assume:
- `tenant_id` exists on every raw table
- timestamps can be cast into `TIMESTAMP` safely
- raw schema name is `raw_shared` (shared dataset approach)

If you choose a per-tenant dataset approach instead, the dbt `source()` definitions would change accordingly.
