# Drivepoint Retail Cloud — Multi-Tenant Commerce+Finance Pipeline (Design)

## Goals
- Ingest raw Shopify + QuickBooks data via Airbyte into BigQuery
- Transform with dbt into BI-ready marts (Looker/PowerBI/Connected Sheets)
- Support 100s of tenants safely (no cross-tenant exposure)
- Reliability + observability by design, not by “more code”

---

## 1) Tenancy Strategy in BigQuery (Isolation model)

### Option A (Recommended default): Shared datasets + `tenant_id` + Row-Level Security (RLS)
**Shape**
- Raw: `bq_project.raw_shared.*` where each table includes `tenant_id`
- Analytics: `bq_project.analytics_shared.*` with facts/dims including `tenant_id`
- Use BigQuery Row Access Policies (RLS) or Authorized Views for tenant isolation.

**Pros**
- Lowest operational overhead at 100s of tenants
- Efficient dbt runs (single set of models)
- Easy to add new tenants (config + policies)

**Cons**
- Security depends on correct RLS/authorized views (must be rigorously tested)
- Requires discipline: every model must propagate tenant_id and never “drop it”

**Cost**
- Generally lowest: fewer datasets, fewer duplicated tables

### Option B: Per-tenant dataset (e.g., `raw_tna_aloe`, `analytics_tna_aloe`)
**Pros**
- Strong isolation boundary; simpler mental model
- Less reliance on RLS correctness

**Cons**
- High overhead with 100s of tenants (datasets, permissions, dbt runs, CI)
- Higher cost due to duplicated storage + compute
- Harder to manage schema evolution across tenants

### Option C: Hybrid
- Shared raw + per-tenant analytics, or vice versa
- Use for very large tenants or regulated customers (“enterprise tier”)

**Decision**
- Default to **Option A**; offer **Option C** for enterprise.

---

## 2) Data Contracts (future sources: Amazon, Netsuite)
- Standardize on a canonical set of **source contracts** per domain:
  - Commerce: orders, line_items, refunds, customers, products
  - Finance: expenses, invoices, payments, chart_of_accounts
- Contract fields:
  - `tenant_id`, `source_system`, `source_record_id`, `updated_at`, `ingested_at`
  - domain-specific required fields + types
- Enforce with:
  - dbt **source freshness** + **schema tests** (not_null, unique, accepted_values)
  - dbt **contracts** on staging models (where supported) and CI checks
- Add new connectors by mapping into canonical staging models:
  - `stg_amazon_orders` -> `int_orders_unified`
  - `stg_netsuite_expenses` -> `int_finance_unified`

---

## 3) Reliable, fault-tolerant pipeline (Airflow orchestration)

### Orchestration pattern
- Tenants are configuration-driven (control table / Airflow Variable)
- DAG dynamically maps tasks across tenants:
  1) Trigger Airbyte sync (Shopify + QuickBooks)
  2) Wait/sense for completion with timeouts
  3) Run dbt build for shared analytics (or subset)
  4) Run tests / validations
  5) Emit metrics + alert on failures

### Failure handling
- Airbyte failures are isolated per tenant+source:
  - One tenant failing should not block others from loading raw
- dbt failures:
  - If shared dataset: fail the run, alert, and optionally “continue building unaffected models” by splitting dbt selection
- Retries:
  - Retry transient failures automatically (network/API)
  - Avoid infinite retries; escalate via PagerDuty/Slack

### Operational metrics
- Store pipeline run logs in an ops table in BigQuery:
  - `ops.pipeline_task_runs` (tenant_id, source, task_name, status, duration_sec, rows_loaded, error)
- Emit:
  - task durations, row counts, row deltas (from dbt artifacts), freshness lag

---

## 4) Data Quality Approach
- At raw layer:
  - basic ingestion checks: “table exists”, “rows increased or updated_at progressed”
  - source freshness checks (dbt source freshness)
- At staging/intermediate:
  - uniqueness / PK checks (order_id, txn_id)
  - accepted values (currency, financial_status)
  - referential integrity (line_items.order_id exists in orders)
- At marts:
  - reconciliation checks: sales totals vs raw orders totals within tolerance
  - anomaly detection (optional): sudden drops/spikes per tenant

Tooling:
- dbt tests + Great Expectations (optional) for more complex validations
- Airflow SLA alerts + centralized logs/metrics

---

## 5) Observability & Alerting
- Centralized logging (Cloud Logging)
- Metrics (Cloud Monitoring / StatsD) keyed by:
  - `tenant_id`, `source`, `dag_id`, `task_id`
- Alert routes:
  - Drivepoint on-call: global failures, dbt failures, widespread Airbyte failures
  - Tenant support channel: tenant-specific repeated failures

---

## 6) DBT Setup

### Directory structure
- `models/staging/{shopify,quickbooks}`: source-normalized, 1:1-ish with raw
- `models/intermediate`: unify logic, join, dedupe, normalize
- `models/marts`: BI facts/dims

### dbt Cloud vs dbt Core
- **dbt Core**: more control, runs inside Airflow/K8s, simpler cost
- **dbt Cloud**: managed scheduling, docs hosting, easier governance
Decision:
- If Airflow is source of truth for orchestration, dbt Core is fine.
- dbt Cloud is great if org wants managed UX + lineage + job separation.

### Views vs tables vs incremental
- Staging: views (fast iteration, low storage)
- Intermediate: tables for expensive joins/dedup; incremental if large
- Marts:
  - `fct_sales_by_day`: incremental (partition by date, cluster by tenant_id)
  - `fct_expenses_by_month`: incremental (partition by month, cluster by tenant_id)

### Performance / cost controls
- Partition + cluster facts by `date` and `tenant_id`
- Incremental models with `updated_at` watermark
- Limit scanned data: filter by execution window + tenant partition
- Use dbt `--select state:modified+` in CI
- Materialize stable dims as tables; keep volatile staging as views

### Testing approach
- Required tests in CI:
  - not_null, unique, accepted_values, relationships
- Smoke tests per PR; full suite nightly

---

## 7) Security & access for Connected Sheets + direct BigQuery access

### Requirement: Each tenant only sees their rows
Recommended approach (shared datasets):
1) Create a **Google Group per tenant** (e.g., `tna_aloe_analysts@`)
2) Grant dataset access to shared analytics dataset (read only)
3) Enforce row security:
   - BigQuery Row Access Policies on each fact/dim keyed by tenant_id
   - Policy filters by group membership -> tenant_id
4) For Connected Sheets:
   - Use the secured tables/views (RLS applied) to power sheets
   - Provide two templates per tenant:
     - Sales by Day -> `analytics_shared.fct_sales_by_day`
     - Expenses per Month -> `analytics_shared.fct_expenses_by_month`

### Drivepoint admins
- Admin group bypasses RLS or has a policy that returns all rows
- Auditing via BigQuery logs: who queried what

### Let customers query directly
- Give tenant analyst group:
  - `bigquery.dataViewer` on dataset
  - `bigquery.jobUser` to run queries
- Optional: expose **Authorized Views** instead of raw tables for extra safety

## Architecture Overview (Diagram)

![Architecture Overview](docs/architecture_overview.svg)
