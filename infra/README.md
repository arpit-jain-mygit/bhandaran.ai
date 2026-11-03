# infra - Terraform for bhandaran.ai (T0)

All AWS infrastructure is created from code in this folder. Region: **ap-south-1 (Mumbai)**.

## Contents

- [Layout](#layout)
- [What gets created](#what-gets-created)
- [Prerequisites](#prerequisites)
- [First-time setup](#first-time-setup)
- [Day-to-day use](#day-to-day-use)
- [CI (GitHub Actions)](#ci-github-actions)
- [Cost](#cost)
- [Tear down dev](#tear-down-dev)

## Layout

```
infra/
├── bootstrap/          one-time: S3 bucket for Terraform state (local state)
├── modules/
│   ├── dsql/           Aurora DSQL cluster
│   ├── s3_bucket/      private, encrypted bucket (warehouse photos)
│   ├── github_oidc/    GitHub Actions -> AWS roles (no stored keys)
│   ├── cost_alarms/    monthly budget + DSQL daily DPU alarm
│   ├── api_lambda/     FastAPI on Lambda + API Gateway HTTP API
│   ├── web_hosting/    S3 + CloudFront (UI at /, API at /api/*)
│   └── github_deploy_role/  narrow role for app deploys
└── envs/
    ├── shared/         once per account: CI roles, monthly budget
    ├── dev/            DSQL, photos bucket, DPU alarm, hosting, deploy role
    └── prod/           same as dev, safer settings (applied at M14)
```

## What gets created

| Stack | Resources | Notes |
|---|---|---|
| bootstrap | `bhandaran-tfstate-<account>` S3 bucket | Versioned, encrypted, HTTPS only, `prevent_destroy` |
| shared | `bhandaran-github-plan` role (read-only), `bhandaran-github-apply` role (admin, main branch only), monthly budget | Reuses the account's existing GitHub OIDC provider |
| dev | DSQL cluster `bhandaran-dev`, bucket `bhandaran-dev-photos-<account>`, SNS topic + daily DPU alarm | No VPC/NAT needed: DSQL uses IAM auth |
| dev (M0b) | Lambda `bhandaran-dev-api` + HTTP API (10 req/s, burst 20), web bucket, CloudFront distribution + SPA function, `bhandaran-dev-github-deploy` role | Dev URL: `terraform output web_url` |
| prod | Same as dev with deletion protection and no `force_destroy` | **Not applied in T0** |

## Prerequisites

- Terraform >= 1.10 (S3 native locking)
- AWS CLI logged in to the target account (`aws sts get-caller-identity`)

## First-time setup

**1. Bootstrap the state bucket** (once per account):

```bash
terraform -chdir=infra/bootstrap init
```

```bash
terraform -chdir=infra/bootstrap apply
```

Note the `state_bucket_name` output.

**2. Configure each stack** (shared, dev): copy the examples and fill in values.

```bash
cp infra/envs/shared/backend.hcl.example infra/envs/shared/backend.hcl
```

```bash
cp infra/envs/shared/terraform.tfvars.example infra/envs/shared/terraform.tfvars
```

Repeat for `infra/envs/dev`. Both files are git-ignored.

**3. Apply shared, then dev:**

```bash
terraform -chdir=infra/envs/shared init -backend-config=backend.hcl
```

```bash
terraform -chdir=infra/envs/shared apply
```

```bash
terraform -chdir=infra/envs/dev init -backend-config=backend.hcl
```

```bash
terraform -chdir=infra/envs/dev apply
```

**4. Confirm the alert emails.** AWS SNS sends a "Subscription Confirmation" email - click the link, or DPU alarms will not be delivered.

**5. Activate the cost tag.** In Billing -> Cost allocation tags, activate the `project` tag (it appears ~24h after the first tagged resource exists). Until then the budget shows $0.

## Day-to-day use

```bash
terraform -chdir=infra/envs/dev plan
```

```bash
terraform fmt -recursive infra
```

Useful dev outputs for the FastAPI config:

```bash
terraform -chdir=infra/envs/dev output
```

## CI (GitHub Actions)

Workflow: [.github/workflows/terraform.yml](../.github/workflows/terraform.yml)

- **Pull request**: `fmt` check and `validate` for all stacks; `plan` for dev using the read-only role.
- **Manual run** (Actions -> terraform -> Run workflow, on `main`): `apply` the chosen stack using the admin role.
- **App deploy** ([deploy-dev.yml](../.github/workflows/deploy-dev.yml)): after `ci` passes on `main`, uploads the API to Lambda and the web build to S3, clears CloudFront, smoke-tests `/api/health`. Terraform is not involved: Lambda code is ignored by Terraform after the first apply.

Set these repository variables (Settings -> Secrets and variables -> Actions -> Variables):

| Variable | Value |
|---|---|
| `AWS_PLAN_ROLE_ARN` | `github_plan_role_arn` output of shared |
| `AWS_APPLY_ROLE_ARN` | `github_apply_role_arn` output of shared |
| `TF_STATE_BUCKET` | bootstrap `state_bucket_name` output |
| `ALERT_EMAIL` | email for cost alerts |
| `AWS_DEV_DEPLOY_ROLE_ARN` | dev `github_deploy_role_arn` output |
| `DEV_API_FUNCTION` | dev `api_function_name` output |
| `DEV_WEB_BUCKET` | dev `web_bucket_name` output |
| `DEV_CLOUDFRONT_ID` | dev `cloudfront_distribution_id` output |
| `DEV_WEB_URL` | dev `web_url` output |

## Cost

| Item | Expected monthly cost |
|---|---|
| DSQL (idle / light dev use) | ~$0 (free tier: 100k DPU + 1 GB) |
| S3 (state + a few photos) | < $0.10 |
| SNS email, CloudWatch alarm, Budget | ~$0 (within free tiers) |
| Lambda, API Gateway, CloudFront (dev traffic) | ~$0-1 |
| IAM / OIDC | free |

The **monthly budget** (default $10) and **daily DPU alarm** (default 10,000 DPU/day) email you before costs grow.

## Tear down dev

```bash
terraform -chdir=infra/envs/dev destroy
```

Dev has deletion protection off and `force_destroy` on, so this removes the cluster and photos. The state bucket (bootstrap) is protected and stays.
