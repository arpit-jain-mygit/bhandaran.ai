# backend - FastAPI API for bhandaran.ai

## Contents

- [Layout](#layout)
- [Setup](#setup)
- [Run](#run)
- [Database modes](#database-modes)
- [Migrations](#migrations)
- [DSQL rules for migrations](#dsql-rules-for-migrations)
- [Master data API](#master-data-api)
- [Checks](#checks)
- [Lambda build](#lambda-build)

## Layout

```
backend/
├── app/
│   ├── main.py          FastAPI app, CORS, router registration
│   ├── config.py        settings from env vars / .env
│   ├── db.py            engine for local Postgres or Aurora DSQL
│   ├── auth.py          temporary admin-key check (until M3)
│   ├── models/          SQLAlchemy tables (base mixins, master data)
│   ├── schemas/         request/response shapes (Pydantic)
│   ├── api/health.py    GET /api/health
│   ├── api/master.py    master-data API (M1)
│   └── lambda_handler.py  AWS Lambda entry (Mangum)
├── scripts/build_lambda.sh  builds dist/lambda.zip (Linux arm64)
├── migrations/          Alembic (env.py handles DSQL rules)
├── tests/               pytest (real Postgres test DB, rebuilt each run)
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

```bash
createdb bhandaran_test
```

`bhandaran_test` is wiped and rebuilt from the migrations on every test run (tests refuse any database not named `*_test`).

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
- **Revision IDs must be ≤ 32 characters** (`alembic_version` column size; `tests/test_migrations.py` enforces it).
- Changing an existing table: `ADD COLUMN` takes no constraints; add foreign keys / CHECKs later (DSQL creates them `NOT VALID`), then `ALTER TABLE ASYNC ... VALIDATE CONSTRAINT`. There is no `SET NOT NULL` - use a `CHECK (col IS NOT NULL)`. See migrations 0009-0016 for the pattern.
- When a migration removes something the **running** app still uses, apply it in two phases: additive steps first, deploy the new code, then the removal.

## Master data API

| Method | Path | Who |
|---|---|---|
| GET | `/api/master/{kind}?include_inactive=false` | anyone |
| POST | `/api/master/{kind}` `{code, name, sort_order}` | admin |
| PATCH | `/api/master/{kind}/{id}` `{name?, sort_order?, is_active?}` | admin |
| GET | `/api/master/districts?state_id=&include_inactive=false` | anyone |
| POST | `/api/master/districts` `{state_id, name}` | admin |
| PATCH | `/api/master/districts/{id}` `{name?, is_active?}` | admin |
| GET | `/api/master/cities?district_id=&state_id=&include_inactive=false` | anyone |
| POST | `/api/master/cities` `{district_id, name}` | admin |
| PATCH | `/api/master/cities/{id}` `{name?, is_active?}` | admin |

`kind` = `stock-types`, `storage-types`, `units`, `states`. Locations nest **state → district → city / town**; town names are unique within a district (the same name may exist in two districts). Nothing is deleted: send `{"is_active": false}` to disable.

**Admin = temporary key** (until M3 login): send header `X-Admin-Key` matching `ADMIN_API_KEY` (local: `backend/.env`; dev: `terraform -chdir=../infra/envs/dev output -raw admin_api_key`). In the web app, paste it into the key box on **Admin**.

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
