# SETUP - build bhandaran.ai in a new AWS account

A step-by-step runbook to recreate **everything** in a fresh AWS account: Terraform state, CI roles, budget, the dev database, hosting, and the first deploy. Written so a person **or an AI coding agent** can follow it top to bottom.

## Contents

- [Rules for AI agents](#rules-for-ai-agents)
- [What gets built](#what-gets-built)
- [0. Prerequisites](#0-prerequisites)
- [1. Confirm the target account](#1-confirm-the-target-account)
- [2. Collect inputs](#2-collect-inputs)
- [3. Bootstrap the state bucket](#3-bootstrap-the-state-bucket)
- [4. Shared stack: CI roles + budget](#4-shared-stack-ci-roles--budget)
- [5. Dev stack: database + hosting](#5-dev-stack-database--hosting)
- [6. Run database migrations](#6-run-database-migrations)
- [7. Point GitHub at the new account](#7-point-github-at-the-new-account)
- [8. First deploy](#8-first-deploy)
- [9. Verify](#9-verify)
- [10. Manual follow-ups](#10-manual-follow-ups)
- [11. Update docs and local config](#11-update-docs-and-local-config)
- [12. Optional: retire the old account](#12-optional-retire-the-old-account)
- [13. Delete test data](#13-delete-test-data)
- [14. Manage accounts from the command line](#14-manage-accounts-from-the-command-line)
- [Using a region other than ap-south-1](#using-a-region-other-than-ap-south-1)
- [Troubleshooting](#troubleshooting)

## Rules for AI agents

1. **Run commands from the repo root** (`bhandaran.ai/`) unless a step says otherwise.
2. **Confirm the AWS account ID with the human before the first `terraform apply`** (step 1). Never apply to an account the human did not name.
3. **Never commit** `backend.hcl`, `terraform.tfvars`, `.env`, `*.tfstate`, or `backend/dist/` - they are git-ignored on purpose.
4. Each step ends with a **Check**. Do not continue until the check passes.
5. If an `apply` is blocked by your tool's permission system (IAM roles are created in steps 4 and 5), **stop and ask the human** to run that exact command - do not try another way around it.
6. Step 12 (deleting the old account's resources) is **destructive**: only do it when the human explicitly asks.
7. Step 13 (deleting test data) is **destructive**: prepare the check, but the human clicks **Delete permanently** themselves.

## What gets built

| Order | Stack (`infra/...`) | Creates | Approx. cost |
|---|---|---|---|
| 3 | `bootstrap` | S3 bucket `bhandaran-tfstate-<account>` for Terraform state | ~$0 |
| 4 | `envs/shared` | GitHub OIDC provider (if missing), `bhandaran-github-plan` + `bhandaran-github-apply` roles, $10 monthly budget | $0 |
| 5 | `envs/dev` | Aurora DSQL cluster, photos bucket, DPU alarm + SNS email, Lambda API + API Gateway, web bucket + CloudFront, `bhandaran-dev-github-deploy` role | ~$0-1/month idle |
| - | `envs/prod` | Same as dev with protections - **not applied until M14** | - |

Order matters: **bootstrap → shared → dev**. Dev reads the GitHub OIDC provider that shared creates.

## 0. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Terraform | >= 1.10 | `terraform version` |
| AWS CLI | v2 | `aws --version` |
| Python | >= 3.12, with pip | `python3 --version` |
| Node.js | 22.22+, 24.15+, or 26+ | `node -v` |
| GitHub CLI | any, logged in with repo admin rights | `gh auth status` |
| zip | any | `zip -v` |

AWS credentials for the **new** account with administrator access (SSO profile or access keys). If you use a named profile, export it so every command below uses it:

```bash
export AWS_PROFILE=<new-account-profile>
```

Clone the repo if needed:

```bash
gh repo clone arpit-jain-mygit/bhandaran.ai && cd bhandaran.ai
```

## 1. Confirm the target account

```bash
aws sts get-caller-identity --query '[Account,Arn]' --output text
```

**Check:** show the account ID to the human and get a "yes" before continuing.

Aurora DSQL must be available in the region (ap-south-1 by default):

```bash
aws dsql list-clusters --region ap-south-1 --query 'clusters' --output text
```

**Check:** the command succeeds (an empty result is fine). An "unknown service" or endpoint error means DSQL is not offered there - see [Using a region other than ap-south-1](#using-a-region-other-than-ap-south-1).

## 2. Collect inputs

You need three values:

| Input | How to get it |
|---|---|
| **Alert email** | Ask the human (budget + DPU alarm emails go here) |
| **OIDC provider exists?** | Command below |
| **GitHub OIDC subject prefix** | Command below |

Does the new account already have a GitHub OIDC provider?

```bash
aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[].Arn' --output text | tr '\t' '\n' | grep -c token.actions.githubusercontent.com
```

- `0` → set `create_oidc_provider = true` in step 4.
- `1` → leave it `false` (reuse it).

GitHub's OIDC subject prefix for this repo:

```bash
gh api repos/arpit-jain-mygit/bhandaran.ai/actions/oidc/customization/sub --jq '.sub_claim_prefix // "repo:arpit-jain-mygit/bhandaran.ai"'
```

**Check:** the value matches the `github_subject_prefix` default in `infra/envs/shared/variables.tf` and `infra/envs/dev/variables.tf` (currently `repo:arpit-jain-mygit@250862261/bhandaran.ai@1444180371`). If it differs (repo renamed or moved), update both defaults. A wrong prefix makes every GitHub → AWS login fail with *Not authorized to perform sts:AssumeRoleWithWebIdentity*.

## 3. Bootstrap the state bucket

Bootstrap keeps its own small state **locally** in `infra/bootstrap/`. If an old `terraform.tfstate` from another account is there, move it away first:

```bash
ls infra/bootstrap/terraform.tfstate* 2>/dev/null
```

If files are listed, rename them (do **not** delete - they belong to the old account):

```bash
mkdir -p ~/bhandaran-old-account-state && mv infra/bootstrap/terraform.tfstate* ~/bhandaran-old-account-state/
```

Then:

```bash
terraform -chdir=infra/bootstrap init -input=false
```

```bash
terraform -chdir=infra/bootstrap apply -input=false
```

**Check:**

```bash
terraform -chdir=infra/bootstrap output -raw state_bucket_name
```

Expected: `bhandaran-tfstate-<new-account-id>`.

## 4. Shared stack: CI roles + budget

Write the backend config and variables (both git-ignored). Replace `<ALERT_EMAIL>` and set `<true|false>` from step 2:

```bash
echo "bucket = \"$(terraform -chdir=infra/bootstrap output -raw state_bucket_name)\"" > infra/envs/shared/backend.hcl
```

```bash
printf 'state_bucket_name    = "%s"\nalert_email          = "%s"\nmonthly_budget_usd   = 10\ncreate_oidc_provider = %s\n' "$(terraform -chdir=infra/bootstrap output -raw state_bucket_name)" "<ALERT_EMAIL>" "<true|false>" > infra/envs/shared/terraform.tfvars
```

`-reconfigure` makes Terraform forget any backend from the old account:

```bash
terraform -chdir=infra/envs/shared init -input=false -reconfigure -backend-config=backend.hcl
```

```bash
terraform -chdir=infra/envs/shared apply -input=false
```

**Check:**

```bash
terraform -chdir=infra/envs/shared output
```

Expected: `github_plan_role_arn` and `github_apply_role_arn` with the new account ID.

## 5. Dev stack: database + hosting

```bash
cp infra/envs/shared/backend.hcl infra/envs/dev/backend.hcl
```

Replace `<ALERT_EMAIL>`:

```bash
printf 'alert_email              = "%s"\nphoto_cors_origins       = ["http://localhost:4200"]\ndsql_daily_dpu_threshold = 10000\n' "<ALERT_EMAIL>" > infra/envs/dev/terraform.tfvars
```

```bash
terraform -chdir=infra/envs/dev init -input=false -reconfigure -backend-config=backend.hcl
```

```bash
terraform -chdir=infra/envs/dev apply -input=false
```

This takes ~5-10 minutes (CloudFront is the slow part). About 35 resources are created.

**Check:**

```bash
terraform -chdir=infra/envs/dev output
```

Expected: `dsql_endpoint`, `web_url`, `api_function_name`, `web_bucket_name`, `cloudfront_distribution_id`, `github_deploy_role_arn`, `photos_bucket_name`.

At this point `web_url` shows nothing useful yet: the Lambda holds a placeholder (returns 503) and the web bucket is empty until step 8.

## 6. Run database migrations

Migrations are **not** run by CI; run them from your machine against the new DSQL cluster (IAM auth uses your AWS credentials).

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -q -e ".[dev]" && cd ..
```

```bash
cd backend && DB_MODE=dsql DSQL_ENDPOINT="$(terraform -chdir=../infra/envs/dev output -raw dsql_endpoint)" .venv/bin/alembic upgrade head && cd ..
```

**Check:**

```bash
cd backend && DB_MODE=dsql DSQL_ENDPOINT="$(terraform -chdir=../infra/envs/dev output -raw dsql_endpoint)" .venv/bin/alembic current && cd ..
```

Expected: the latest revision followed by `(head)`.

## 7. Point GitHub at the new account

The workflows read these **repository variables** (not secrets). This overwrites the old account's values:

```bash
R=arpit-jain-mygit/bhandaran.ai; S=infra/envs/shared; D=infra/envs/dev; gh variable set TF_STATE_BUCKET -R $R -b "$(terraform -chdir=infra/bootstrap output -raw state_bucket_name)" && gh variable set AWS_PLAN_ROLE_ARN -R $R -b "$(terraform -chdir=$S output -raw github_plan_role_arn)" && gh variable set AWS_APPLY_ROLE_ARN -R $R -b "$(terraform -chdir=$S output -raw github_apply_role_arn)" && gh variable set AWS_DEV_DEPLOY_ROLE_ARN -R $R -b "$(terraform -chdir=$D output -raw github_deploy_role_arn)" && gh variable set DEV_API_FUNCTION -R $R -b "$(terraform -chdir=$D output -raw api_function_name)" && gh variable set DEV_WEB_BUCKET -R $R -b "$(terraform -chdir=$D output -raw web_bucket_name)" && gh variable set DEV_CLOUDFRONT_ID -R $R -b "$(terraform -chdir=$D output -raw cloudfront_distribution_id)" && gh variable set DEV_WEB_URL -R $R -b "$(terraform -chdir=$D output -raw web_url)"
```

`ALERT_EMAIL` only needs changing if the email changed:

```bash
gh variable set ALERT_EMAIL -R arpit-jain-mygit/bhandaran.ai -b "<ALERT_EMAIL>"
```

**Check:**

```bash
gh variable list -R arpit-jain-mygit/bhandaran.ai
```

Expected: 9 variables; every ARN/bucket contains the **new** account ID.

| Variable | Used by | Source |
|---|---|---|
| `TF_STATE_BUCKET` | terraform.yml | bootstrap `state_bucket_name` |
| `AWS_PLAN_ROLE_ARN` | terraform.yml (PR plan) | shared `github_plan_role_arn` |
| `AWS_APPLY_ROLE_ARN` | terraform.yml (manual apply) | shared `github_apply_role_arn` |
| `ALERT_EMAIL` | terraform.yml | the human |
| `AWS_DEV_DEPLOY_ROLE_ARN` | deploy-dev.yml | dev `github_deploy_role_arn` |
| `DEV_API_FUNCTION` | deploy-dev.yml | dev `api_function_name` |
| `DEV_WEB_BUCKET` | deploy-dev.yml | dev `web_bucket_name` |
| `DEV_CLOUDFRONT_ID` | deploy-dev.yml | dev `cloudfront_distribution_id` |
| `DEV_WEB_URL` | deploy-dev.yml (smoke test) | dev `web_url` |

## 8. First deploy

Run the deploy workflow on `main` (builds the API zip and Angular app, uploads both, clears CloudFront, smoke-tests):

```bash
gh workflow run deploy-dev -R arpit-jain-mygit/bhandaran.ai --ref main
```

```bash
sleep 10 && gh run watch -R arpit-jain-mygit/bhandaran.ai --exit-status $(gh run list -R arpit-jain-mygit/bhandaran.ai -w deploy-dev -L 1 --json databaseId --jq '.[0].databaseId')
```

**Check:** the run ends with all steps green, including **Smoke test**.

<details>
<summary>Fallback: deploy from your machine (if GitHub Actions is unavailable)</summary>

```bash
./backend/scripts/build_lambda.sh
```

```bash
aws lambda update-function-code --function-name "$(terraform -chdir=infra/envs/dev output -raw api_function_name)" --zip-file fileb://backend/dist/lambda.zip --query LastUpdateStatus --output text
```

```bash
aws lambda wait function-updated-v2 --function-name "$(terraform -chdir=infra/envs/dev output -raw api_function_name)"
```

```bash
cd frontend && npm ci && npx ng build && cd ..
```

```bash
aws s3 sync frontend/dist/frontend/browser "s3://$(terraform -chdir=infra/envs/dev output -raw web_bucket_name)" --delete
```

```bash
aws cloudfront create-invalidation --distribution-id "$(terraform -chdir=infra/envs/dev output -raw cloudfront_distribution_id)" --paths "/*" --query Invalidation.Status --output text
```

</details>

## 9. Verify

```bash
curl -s "$(terraform -chdir=infra/envs/dev output -raw web_url)/api/health"
```

Expected:

```json
{"status":"ok","version":"0.1.0","db_mode":"dsql","database":"ok"}
```

```bash
curl -s -o /dev/null -w '%{http_code}\n' "$(terraform -chdir=infra/envs/dev output -raw web_url)/any/deep/link"
```

Expected: `200` (Angular routes are served by CloudFront).

Open the `web_url` in a browser: the **System status** card should show **API ok** and **Database ok (dsql)**, and the **Find storage space** dropdowns should list states, storage types and stock types.

Admin screens (`<web_url>/admin/master-data`) need the temporary admin key (until M3 login). Give it to the human - do not paste it into chat logs or commits:

```bash
terraform -chdir=infra/envs/dev output -raw admin_api_key
```

## 10. Manual follow-ups

These need a human in a browser - an agent should list them for the human:

| What | Where | Why |
|---|---|---|
| **Confirm the SNS email** ("AWS Notification - Subscription Confirmation") | The alert inbox | Without it, DSQL DPU alarms are never delivered |
| **Activate the `project` cost allocation tag** (~24h after step 5) | AWS Billing → Cost allocation tags | The budget only counts resources tagged `project=bhandaran`; until activated it shows $0 |

Check the SNS subscription after the human clicks the link:

```bash
aws sns list-subscriptions --query "Subscriptions[?contains(TopicArn,'bhandaran-dev-cost-alerts')].SubscriptionArn" --output text
```

Expected: an ARN (not `PendingConfirmation`).

## 11. Update docs and local config

The dev URL and IDs are written in a few places. Replace the old values with the new outputs:

| File | What to change |
|---|---|
| `README.md` | Dev environment URL → new `web_url` |
| `MVP.md` | M0b "Done when" URL → new `web_url` |
| `backend/.env` (local, git-ignored) | `DSQL_ENDPOINT` → new `dsql_endpoint` |

Find any leftovers of the old account (replace `<OLD_ACCOUNT_ID>`):

```bash
grep -rn "<OLD_ACCOUNT_ID>\|cloudfront.net" --include='*.md' --exclude-dir=node_modules .
```

Then commit the doc changes (not the git-ignored files).

## 12. Optional: retire the old account

**Destructive - only when the human explicitly asks.** Use the **old** account's credentials, and the old `backend.hcl`/`terraform.tfvars` values (bucket `bhandaran-tfstate-<OLD_ACCOUNT_ID>`).

1. `terraform -chdir=infra/envs/dev destroy` (dev has deletion protection off and `force_destroy` on, so the DSQL cluster and buckets go too).
2. `terraform -chdir=infra/envs/shared destroy` (keeps the OIDC provider if `create_oidc_provider` was `false`).
3. The state bucket has `prevent_destroy`: empty it and delete it in the console, or temporarily remove the `lifecycle` block in `infra/bootstrap/main.tf`, destroy, then restore the block.

## 13. Delete test data

Removes test accounts and godowns from the dev database. **Destructive and not reversible** - the human runs the delete step.

Only an **admin** can do this. Admins are created with the CLI (`create-admin`), not in the app.

1. Log in at `<web_url>/login` with an admin email. The 6-digit code is emailed to that address.
2. Open `<web_url>/admin/test-data`, or pick **Delete test data** in the admin menu.
3. Enter the emails of the accounts to remove, separated by commas or new lines.
4. To remove a single godown, also enter its ID. The ID is the last part of the godown's address, for example `/owner/warehouses/<id>`.
5. Click **Check what will be removed** and read the list. Nothing is deleted yet.
6. Type `DELETE` in the box (exactly, in capitals) and click **Delete permanently**.
7. Read the summary. Any "not found" emails or IDs were already gone or never existed.

What gets removed:

- **An account:** its roles, login codes, owner settings, and mail suppression entries.
- **An owner's godowns:** the godowns, their stock types, their photos (the files in S3 too), and all their bookings.
- **A renter's bookings:** the bookings they hold.
- **Renters an owner invited:** they are kept, but no longer linked to that owner.

Rules that protect you:

- An admin **cannot delete their own account**. To remove an admin, log in as a different admin.
- The delete step only works after a check, and only if the inputs have not changed since the check.

**Check:** run step 5 again with the same emails. Each deleted account now shows under "not found".

## 14. Manage accounts from the command line

Create, list, update and delete **admins, owners and renters** with `app.cli`. The commands run on your laptop against the dev database. They use the same rules as the app: an account's godowns, bookings and photos go with it when it is deleted (see step 13).

Point the shell at dev once, from the repo root:

```bash
cd backend
export DB_MODE=dsql
export DSQL_ENDPOINT="$(terraform -chdir=../infra/envs/dev output -raw dsql_endpoint)"
export PHOTO_BUCKET="$(terraform -chdir=../infra/envs/dev output -raw photos_bucket_name)"
```

| Action | Command | Notes |
|---|---|---|
| Create admin | `.venv/bin/python -m app.cli create-admin --email <email> --name "<name>"` | |
| Create owner | `.venv/bin/python -m app.cli create-owner --email <email> --name "<name>"` | |
| Create renter | `.venv/bin/python -m app.cli create-renter --email <email> --name "<name>"` | |
| List admins | `.venv/bin/python -m app.cli list-admins` | Also `list-owners`, `list-renters` |
| Update name or status | `.venv/bin/python -m app.cli update-account --email <email> --role ADMIN --status SUSPENDED` | `--role` is `ADMIN`, `OWNER` or `RENTER`. Add `--name "<name>"` to rename. `SUSPENDED` blocks login; `ACTIVE` restores it |
| Delete admin | `.venv/bin/python -m app.cli delete-admin --email <email>` | Preview only. Add `--yes` to delete |
| Delete owner | `.venv/bin/python -m app.cli delete-owner --email <email>` | Preview only. Add `--yes` to delete |
| Delete renter | `.venv/bin/python -m app.cli delete-renter --email <email>` | Preview only. Add `--yes` to delete |

Rules to know:

- **Create** adds the role to an existing account and leaves the rest alone. Running it twice is safe.
- **Update** needs `--name`, `--status`, or both. It refuses to suspend the only active admin.
- **Delete** runs the preview first. Read it, then run the same command with `--yes`. The account must have the role you name. An account with more than one role is deleted whole, and the preview says so.
- **Photo files:** `PHOTO_BUCKET` must be set before a delete with `--yes` if the account has godown photos. Without it the command refuses and deletes nothing. The export above sets it.
- The last admin can't be deleted. Create the new admin first.
- **Orphaned photos:** if S3 fails to delete a file, the command logs its key and still removes the database rows. Remove the file yourself with `aws s3 rm s3://<photos_bucket_name>/<key>`.
- **Emails don't depend on case.** The command lower-cases them before it looks them up.

Run `unset DB_MODE DSQL_ENDPOINT PHOTO_BUCKET` to point the same shell back at the local database.

## Using a region other than ap-south-1

Check DSQL availability in the target region first (step 1). Then change the region in **all** of these:

| File | Setting |
|---|---|
| `infra/bootstrap/variables.tf` | `region` default |
| `infra/envs/shared/versions.tf`, `infra/envs/dev/versions.tf`, `infra/envs/prod/versions.tf` | `backend "s3"` → `region` |
| `infra/envs/shared/variables.tf`, `infra/envs/dev/variables.tf`, `infra/envs/prod/variables.tf` | `region` default |
| `.github/workflows/terraform.yml`, `.github/workflows/deploy-dev.yml` | `env.AWS_REGION` |
| `backend/app/config.py`, `backend/.env.example` | `aws_region` / `AWS_REGION` |

Lambda `python3.14` on `arm64` and CloudFront `PriceClass_200` work in all common regions.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Not authorized to perform sts:AssumeRoleWithWebIdentity` in a workflow | OIDC subject prefix mismatch, or the job uses `environment:` (changes the token subject) | Re-check step 2's prefix; never add `environment:` to jobs using these roles |
| `EntityAlreadyExists` for the OIDC provider in step 4 | Provider already exists | Set `create_oidc_provider = false` |
| `No OpenIDConnect provider found` in step 5 | Shared stack not applied, or applied with `create_oidc_provider = false` in an account without one | Apply step 4 with the right value first |
| `Invalid count argument` | A `count` depends on a value only known after apply | Use a plain boolean input (see `create_dpu_alarm` in `modules/cost_alarms`) |
| `/api/health` returns `API not deployed yet` (503) | Placeholder Lambda code | Run step 8 |
| `/api/health` shows `"database":"unreachable"` | Lambda can't reach DSQL, or migrations not run | Check the Lambda role has `dsql:DbConnectAdmin` on the cluster; run step 6 |
| Dropdowns empty / `/api/master/...` errors | Migrations not run on the new cluster | Run step 6 |
| Admin screen says "Admin key missing or wrong" | Key not entered or from the old account | Use the new `admin_api_key` output |
| Lambda build: `No matching distribution found for psycopg-binary` | Missing Linux wheel tag | `build_lambda.sh` must pass both `manylinux2014_aarch64` and `manylinux_2_28_aarch64` |
| Terraform `Error acquiring the state lock` | An interrupted run left `*.tflock` in the state bucket | Make sure no other run is active, then `terraform force-unlock <LOCK_ID>` |
| Budget always $0 | Cost tag not activated | Step 10 |
