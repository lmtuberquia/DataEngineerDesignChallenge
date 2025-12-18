# Drivepoint Data Engineer Design Challenge — Multi-Tenant Commerce Finance Pipeline

This repo contains **design-first artifacts** for a multi-tenant pipeline that:
- Ingests raw Shopify + QuickBooks via **Airbyte**
- Lands data in **BigQuery**
- Transforms via **dbt** into BI-ready marts
- Orchestrates via **Airflow**
- Enforces tenant isolation and supports scaling to 100s of tenants

> Note: This is intentionally not a “working infra” repo. The focus is architecture, approach, and clarity.

## Deliverables
1) **Airflow DAG (pseudocode)**  
   - `airflow/dags/drivepoint_multitenant_commerce_finance.py`
2) **Design Doc (~1–2 pages)**  
   - `docs/DESIGN.md`

Optional supporting notes:
- Data contract thinking: `docs/AIRBYTE_CONTRACTS.md`
- dbt project skeleton: `dbt/`

---

## Quick Start (Local)

### Requirements
- Docker + Docker Compose

### Run Airflow locally
```bash
cp .env.example .env
docker compose up --build -d
```

### Airflow UI:
```bash
http://localhost:8080

user/pass: admin/admin
```