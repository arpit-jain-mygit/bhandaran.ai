# bhandaran.ai

A marketplace that connects **godown owners** who rent out storage space with **traders** who need it - with a bag-level stock ledger both sides can trust.

## Contents

- [Repository layout](#repository-layout)
- [Quick start (local)](#quick-start-local)
- [Plan](#plan)

## Repository layout

| Folder | What | Docs |
|---|---|---|
| `infra/` | Terraform for AWS (DSQL, S3, CI roles, cost alarms) | [infra/README.md](infra/README.md) |
| `backend/` | FastAPI API + Alembic migrations | [backend/README.md](backend/README.md) |
| `frontend/` | Angular web app | [frontend/README.md](frontend/README.md) |
| `.github/workflows/` | CI: app checks (`ci.yml`), Terraform (`terraform.yml`) | |

Stack: Angular · FastAPI · Aurora DSQL (PostgreSQL-compatible) · Terraform on AWS (ap-south-1).

## Quick start (local)

Terminal 1 - API on port 8000 (see [backend/README.md](backend/README.md) for first-time setup):

```bash
cd backend && .venv/bin/alembic upgrade head && .venv/bin/uvicorn app.main:app --reload
```

Terminal 2 - web app on port 4200 (calls `/api` through the dev proxy):

```bash
cd frontend && npm install && npx ng serve
```

Open http://localhost:4200 - the System status card should show **API ok** and **Database ok**.

## Plan

- [MVP.md](MVP.md) - Release 1 milestones and status
