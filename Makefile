.PHONY: up down logs fmt

up:
	cp -n .env.example .env || true
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

fmt:
	python -m pip install ruff
	ruff format airflow/dags/drivepoint_multitenant_commerce_finance.py
