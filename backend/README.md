# backend - FastAPI API for bhandaran.ai

## Contents

- [Layout](#layout)
- [Setup](#setup)
- [Run](#run)
- [Database modes](#database-modes)
- [Migrations](#migrations)
- [DSQL rules for migrations](#dsql-rules-for-migrations)
- [Master data API](#master-data-api)
- [Platform settings API](#platform-settings-api)
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
│   ├── api/settings.py  platform-settings API (M2)
│   ├── platform_settings.py  setting list + effective-value rules (M2)
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

## Platform settings API

Each setting is defined in code in `app/platform_settings.py` (type, default, allowed values). The value that applies is the **owner's override**, else the **platform value**, else the **code default**; responses include `source` (`owner` / `platform` / `default`).

| Method | Path | Who |
|---|---|---|
| GET | `/api/settings` | anyone |
| PUT | `/api/settings/{key}` `{value}` | admin |
| DELETE | `/api/settings/{key}` (back to default) | admin |
| GET | `/api/settings/owners/{owner_id}` | anyone (owner-only after M3) |
| PUT | `/api/settings/owners/{owner_id}/{key}` `{value}` | admin for now (the owner after M3/M4) |
| DELETE | `/api/settings/owners/{owner_id}/{key}` | admin for now |

To add a setting, add a `SettingDef` to `SETTINGS` - no migration needed. Code that needs the values calls `effective_settings(session, owner_id)`.

## Checks

```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest -q
```

## Lambda build

In AWS the same app runs on Lambda (`app.lambda_handler.handler`). The CI deploy builds the zip; to build it yourself:

```bash
./scripts/build_lambda.sh
```

It downloads Linux arm64 wheels for Python 3.14 (not your Mac's), so the zip runs on Lambda, and **precompiles every file to bytecode** (`.pyc`, `unchecked-hash`). It must run on Python 3.14 - the script refuses other versions, because `.pyc` files only work on the version that made them.

### Cold starts (measured on dev, 2026-11-03)

Lambda shuts down when idle; the next request waits for it to start ("cold start").

| Setup | What a user waits | Billed per cold start |
|---|---|---|
| Before: 512 MB, no `.pyc` | 6.0 - 7.5 s | 2.7 - 3.5 GB-s |
| **Now: 512 MB + `.pyc`** | **2.8 - 3.1 s** | **1.2 - 1.3 GB-s** (about half) |
| Tried: 1024 MB + `.pyc` | 2.5 - 2.7 s | 1.9 - 2.2 GB-s |
| Tried: 1769 MB (1 full vCPU) + `.pyc` | 1.7 - 1.9 s | 2.3 - 2.5 GB-s |

Why: Lambda's code folder is read-only, so without shipped `.pyc` files Python recompiled every library on each cold start on a fraction of a CPU. We kept **512 MB** - cheapest per cold start; more memory is faster but costs more.

**Keep-warm ping:** an EventBridge schedule sends `{"warmup": true}` every 5 minutes, 05:30-23:30 IST (`infra/modules/api_lambda`, `warmup_schedule`). `app/lambda_handler.py` answers it with one `SELECT 1`, keeping the instance and its DSQL connection warm, so most visitors get a warm response (~0.1-0.3 s). About 6,500 pings a month: inside Lambda's free tier; watch DSQL `TotalDPU` for the small cost of the `SELECT 1`s.
