# bhandaran.ai - MVP (Release 1)

A marketplace that connects **godown owners** (who rent out storage space) with **renters** (traders who store their stock in bags).

**Release 1 goal:** an owner can list a warehouse, add their existing renters offline, and track every bag going in and out - useful even before any renter joins online.

## Contents

- [Personas](#personas)
- [Release 1 scope](#release-1-scope)
- [Milestones](#milestones)
  - [T0 - Terraform foundation](#t0---terraform-foundation)
  - [M0 - App foundation](#m0---app-foundation)
  - [M1 - Master data](#m1---master-data)
  - [M2 - Platform config](#m2---platform-config)
  - [M3 - Login](#m3---login)
  - [M4 - Profiles](#m4---profiles)
  - [M5 - Warehouse listing](#m5---warehouse-listing)
  - [M6 - Admin review](#m6---admin-review)
  - [M7 - Search](#m7---search)
  - [M8 - Offline booking](#m8---offline-booking)
  - [M10 - Stock ledger](#m10---stock-ledger)
- [Build order](#build-order)
- [Not in Release 1](#not-in-release-1)
- [Tech stack](#tech-stack)

## Personas

| Persona | Who | In Release 1 |
|---|---|---|
| **Owner** | Godown / cold-storage owner | Lists warehouse, adds offline bookings, records stock IN/OUT |
| **Renter** | Trader, wholesaler, farmer group | Claims account via link, searches warehouses, views own stock |
| **Admin** | bhandaran.ai team | Manages master data and config, reviews listings |

## Release 1 scope

| # | Milestone | Status |
|---|---|---|
| T0 | Terraform foundation | ⬜ |
| M0 | App foundation | ⬜ |
| M1 | Master data | ⬜ |
| M2 | Platform config | ⬜ |
| M3 | Login | ⬜ |
| M4 | Profiles | ⬜ |
| M5 | Warehouse listing | ⬜ |
| M6 | Admin review | ⬜ |
| M7 | Search | ⬜ |
| M8 | Offline booking | ⬜ |
| M10 | Stock ledger | ⬜ |

Status: ⬜ not started · 🟡 in progress · ✅ done

## Milestones

### T0 - Terraform foundation

**Goal:** all AWS infrastructure is created from code.

- Remote Terraform state in S3 (versioned, encrypted, S3 native locking)
- `dev` and `prod` environments sharing modules
- GitHub OIDC role for CI (no stored AWS keys)
- Aurora DSQL cluster (dev), IAM authentication
- Private S3 bucket for warehouse photos
- AWS Budget alarm and DSQL `TotalDPU` alarm

**Done when:** `terraform apply` on `envs/dev` creates the DSQL cluster, photo bucket and alarms from a clean account.

**Depends on:** -

### M0 - App foundation

**Goal:** an empty app runs end to end.

- Angular app shell and FastAPI project
- Local Postgres (Docker) for development, DSQL for integration
- Alembic migrations (one DDL per step, `CREATE INDEX ASYNC`)
- Health-check API, CI pipeline (lint, test)

**Done when:** Angular calls the FastAPI health API, and migrations run against dev DSQL.

**Depends on:** T0

### M1 - Master data

**Goal:** reference lists used by every other feature.

- Stock types (wheat, potato, rice, ...)
- Storage types (dry, cold, open yard)
- Units (bag, sq ft)
- States and cities
- Admin create / edit / disable screens

**Done when:** admin can manage all lists and they appear in dropdowns.

**Depends on:** M0

### M2 - Platform config

**Goal:** behaviour can be changed without code changes.

- Settings with **platform default** and **owner override**
- `offline_booking_requires_renter_confirmation`
- `renter_confirmation_timeout_days`
- `on_timeout_action` (`AUTO_CONFIRM` / `FLAG_UNVERIFIED`)
- `allow_stock_in_before_confirmation`

**Done when:** admin sets defaults, an owner overrides one, and the API returns the effective value.

**Depends on:** M0

### M3 - Login

**Goal:** users sign in with their phone.

- Phone OTP login (mocked OTP in local/dev)
- Roles: OWNER, RENTER, ADMIN
- JWT sessions, role guards in Angular and FastAPI
- Admin accounts created only by an admin or seed

**Done when:** each role logs in and sees only its own screens.

**Depends on:** M0

### M4 - Profiles

**Goal:** owners and renters have profiles; offline renters can be added.

- Owner and renter profile (name, city, optional GST)
- One account per phone number
- **Unclaimed renter**: created by an owner using the renter's phone number
- **Claim flow**: renter opens link, verifies OTP, account becomes active
- No admin review at sign-up

**Done when:** an owner creates an unclaimed renter, and that renter claims the account via OTP.

**Depends on:** M3

### M5 - Warehouse listing

**Goal:** owners describe their space.

- Name, address, city, pincode
- Total capacity and unit, storage type, allowed stock types
- Price per unit per month
- Photo upload to S3 (presigned URLs)
- Status: `DRAFT` → `PENDING_REVIEW`

**Done when:** an owner submits a complete listing for review.

**Depends on:** M1, M4

### M6 - Admin review

**Goal:** only real warehouses go live.

- Review queue with photos, address and "open in Maps" link
- Actions: **Approve** (→ `LIVE`), **Ask for more info**, **Reject** with reason
- Audit log of every decision
- Pluggable check pipeline (`listing_verification`) with one check: `ADMIN_REVIEW`

**Done when:** an approved listing becomes `LIVE`, and every decision is in the audit log.

**Depends on:** M5

### M7 - Search

**Goal:** renters find space.

- Search `LIVE` warehouses by city / pincode
- Filters: storage type, price, available capacity
- Warehouse detail page

**Done when:** a renter finds a live warehouse by city with correct free capacity.

**Depends on:** M6

### M8 - Offline booking

**Goal:** owners record deals made in person or by phone.

- Owner enters booking: renter phone, stock type, capacity, dates, agreed rate
- Renter found by phone, or created as unclaimed
- Capacity check with retry on concurrent writes
- Renter confirmation **as per config** (on / off, timeout, auto-confirm or flag)
- Renter gets a claim / confirm link (logged in Release 1; WhatsApp/SMS later)
- Booking states: `PENDING_RENTER_CONFIRMATION` → `CONFIRMED` → `ACTIVE`

**Done when:** an owner books space for a new renter, capacity reduces, and confirmation follows the config.

**Depends on:** M2, M4, M6

### M10 - Stock ledger

**Goal:** every bag is accounted for.

- **Lot**: one batch of stock under a booking
- **Movements**: IN / OUT with bags, date, remarks
- Stored bag balance per lot and per booking
- OUT larger than balance is blocked
- Ledger visible to owner (edit) and renter (read)

**Done when:** 200 IN, 50 OUT, 50 OUT shows a balance of 100 to both sides, and a 101-bag OUT is rejected.

**Depends on:** M8

## Build order

```
T0  Terraform foundation
 ▼
M0  App foundation
 ├──► M1 Master data ─────┐
 ├──► M2 Platform config  │
 └──► M3 Login            │
        ▼                 │
      M4 Profiles         │
        ▼                 ▼
      M5 Warehouse listing
        ▼
      M6 Admin review
        ├──► M7 Search
        ▼
      M8 Offline booking  (+ M2, M4)
        ▼
      M10 Stock ledger    ══►  Release 1
```

## Not in Release 1

- Online booking requests (M9)
- Charges, dues and statements (M11)
- Real WhatsApp / SMS notifications and 6-monthly statements (M12)
- Report user (M13)
- Production go-live (M14)
- Payments, KYC Level 2-3, disputes, ratings, staff accounts, radius search, languages, mobile app

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Angular |
| Backend | FastAPI (Python) |
| Database | Aurora DSQL (local Postgres for dev) |
| Infrastructure | Terraform on AWS |
| Files | S3 (private, presigned URLs) |
