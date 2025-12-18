from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.utils.trigger_rule import TriggerRule


DEFAULT_ARGS = {
    "owner": "drivepoint",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=45),  # per task hard timeout
}

DAG_ID = "drivepoint_multitenant_commerce_finance"


def _load_tenants() -> List[Dict[str, Any]]:
    """
    Tenants are config-driven.
    - For 100s of tenants: store in a DB table (control plane) or Airflow Variable in JSON,
      refreshed daily (or read from a config service).
    """
    raw = Variable.get("TENANTS_JSON", default_var="[]")
    return json.loads(raw)


with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2025, 1, 1),
    schedule="0 6 * * *",  # daily example
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    doc_md="""
### Drivepoint Multi-Tenant Commerce+Finance Pipeline (Design)

Orchestrates:
1) Airbyte raw sync per tenant (Shopify + QuickBooks)
2) dbt transforms (staging -> intermediate -> marts)
3) quality checks + metrics emission

See /opt/airflow/docs/DESIGN.md for design decisions.
""",
) as dag:

    @task
    def get_tenants() -> List[Dict[str, Any]]:
        tenants = _load_tenants()
        if not tenants:
            raise ValueError("No tenants configured")
        return tenants

    @task
    def trigger_airbyte_sync(tenant: Dict[str, Any], source: str) -> Dict[str, Any]:

        tenant_id = tenant["tenant_id"]
        conn_id = tenant["shopify_conn_id"] if source == "shopify" else tenant["qb_conn_id"]

        # pretend we called Airbyte and got a job id
        job_id = f"job_{tenant_id}_{source}_{{{{ ts_nodash }}}}"

        return {"tenant_id": tenant_id, "source": source, "connection_id": conn_id, "job_id": job_id}

    @task
    def wait_for_airbyte_completion(job: Dict[str, Any]) -> Dict[str, Any]:
        """
        PSEUDOCODE:
        - poll Airbyte job status until SUCCEEDED/FAILED/TIMEOUT
        - enforce sensor timeout separately
        - on failure: return structured error payload for downstream handling
        """
        # Here we just pass through for design.
        return {**job, "status": "SUCCEEDED", "rows_loaded": 1234, "duration_sec": 42}

    @task
    def emit_operational_metrics(results: List[Dict[str, Any]]) -> None:
        """
        Emit metrics/logs:
        - task duration
        - rows loaded
        - rows changed (dbt artifacts)
        - success/failure per tenant & source
        PSEUDOCODE:
        - push to StatsD/Cloud Monitoring
        - write to BigQuery ops schema (ops.pipeline_runs)
        """
        # No-op for design challenge; just structure.
        _ = results

    @task
    def run_dbt_for_all_tenants() -> Dict[str, Any]:
        """
        DBT is run once per schedule, but models must be tenant-safe.
        Two common patterns:
        1) Shared dataset + tenant_id column + row-level security
        2) Per-tenant dataset (strong isolation, higher overhead)
        This DAG assumes shared dataset + RLS as default.

        PSEUDOCODE:
        - dbt deps
        - dbt build --select tag:daily
        - parse run_results.json for metrics (rows affected)
        """
        return {"status": "SUCCEEDED", "models_built": 42, "rows_changed_est": 9001}

    @task
    def dbt_tests_and_contracts() -> Dict[str, Any]:
        """
        PSEUDOCODE:
        - dbt test (generic + singular tests)
        - validate freshness (dbt source freshness) for raw
        - enforce schema contracts for staging
        """
        return {"status": "SUCCEEDED", "tests_passed": 128}

    @task(trigger_rule=TriggerRule.ALL_DONE)
    def failure_handling_and_alerting(
        airbyte_results: List[Dict[str, Any]],
        dbt_result: Dict[str, Any],
        test_result: Dict[str, Any],
    ) -> None:
        """
        PSEUDOCODE:
        - if any failures, create an incident:
          - send Slack / PagerDuty
          - include tenant_id(s), source(s), job_id(s), error links
        - optionally auto-retry only failed tenants (next run or backfill)
        """
        # No-op for design challenge
        _ = (airbyte_results, dbt_result, test_result)

    tenants = get_tenants()

    @task
    def expand_jobs(tenants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        jobs = []
        for t in tenants:
            jobs.append({"tenant": t, "source": "shopify"})
            jobs.append({"tenant": t, "source": "quickbooks"})
        return jobs

    jobs = expand_jobs(tenants)

    @task
    def trigger_job(job: Dict[str, Any]) -> Dict[str, Any]:
        return trigger_airbyte_sync(tenant=job["tenant"], source=job["source"])

    triggered = trigger_job.expand(job=jobs)
    completed = wait_for_airbyte_completion.expand(job=triggered)

    metrics = emit_operational_metrics(completed)

    dbt_run = run_dbt_for_all_tenants()
    dbt_test = dbt_tests_and_contracts()

    metrics >> dbt_run >> dbt_test

    failure_handling_and_alerting(completed, dbt_run, dbt_test)
