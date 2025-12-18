FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /usr/app/dbt

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
 && rm -rf /var/lib/apt/lists/*

# dbt-bigquery (pin ranges are fine for a design challenge)
RUN pip install --no-cache-dir "dbt-core>=1.7,<2.0" "dbt-bigquery>=1.7,<2.0"

CMD ["bash", "-lc", "dbt --version && tail -f /dev/null"]
