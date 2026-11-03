# backend - FastAPI API for bhandaran.ai

## Contents

- [Layout](#layout)
- [Setup](#setup)
- [Run](#run)
- [Database modes](#database-modes)
- [Migrations](#migrations)
- [DSQL rules for migrations](#dsql-rules-for-migrations)
- [Checks](#checks)
- [Lambda build](#lambda-build)

## Layout

```
backend/
├── app/
│   ├── main.py          FastAPI app, CORS, router registration
│   ├── config.py        settings from env vars / .env
│   ├── db.py            engine for local Postgres or Aurora DSQL
│   ├── api/health.py    GET /api/health
│   └── lambda_handler.py  AWS Lambda entry (Mangum)
├── scripts/build_lambda.sh  builds dist/lambda.zip (Linux arm64)
├── migrations/          Alembic (env.py handles DSQL rules)
├── tests/               pytest (no DB needed - fakes)
└── pyproject.toml       dependencies, ruff, pytest config
```

## Setup

Needs Python 3.12+ and a local PostgreSQL (Homebrew `postgresql@15` works).

```bash
cd backend
```

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -e ".[dev]"
```

```bash
cp .env.example .env
```

```bash
createdb bhandaran
```

## Run

```bash
.venv/bin/alembic upgrade head
```

```bash
.venv/bin/uvicorn app.main:app --reload
```

- Health: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

## Database modes

| `DB_MODE` | Database | Auth | Use for |
|---|---|---|---|
| `local` (default) | PostgreSQL on your machine | none | everyday development |
| `dsql` | Aurora DSQL in AWS | IAM token from your AWS credentials | integration checks, prod |

For `dsql`, set `DSQL_ENDPOINT` from:

```bash
terraform -chdir=../infra/envs/dev output -raw dsql_endpoint
```

## Migrations

```bash
.venv/bin/alembic revision -m "create stock_type"
```

```bash
.venv/bin/alembic upgrade head
```

```bash
.venv/bin/alembic current
```

## DSQL rules for migrations

Aurora DSQL is stricter than PostgreSQL. `migrations/env.py` runs in AUTOCOMMIT so each statement is its own transaction, and registers the `auroradsql` dialect with Alembic. When writing migrations:

- **One schema change per migration file.**
- **UUID primary keys** with `server_default=sa.text("gen_random_uuid()")`.
- Indexes are created with `CREATE INDEX ASYNC` (the dialect does this).
- No triggers, PL/pgSQL, extensions (PostGIS), temp tables, `TRUNCATE`, or array columns.
- Data changes (DML) go in a **separate** migration from schema changes (DDL).
- At most 3,000 rows changed per transaction - batch large data migrations.

## Checks

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest -q
```

## Lambda build

In AWS the same app runs on Lambda (`app.lambda_handler.handler`). The CI deploy builds the zip; to build it yourself:

```bash
./scripts/build_lambda.sh
```

It downloads Linux arm64 wheels for Python 3.14 (not your Mac's), so the zip runs on Lambda.
