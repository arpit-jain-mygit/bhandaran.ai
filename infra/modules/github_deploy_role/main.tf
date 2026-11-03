# ---------------------------------------------------------------
# Module: github_deploy_role
# A NARROW role GitHub Actions uses to deploy app code on every push
# to main. Unlike the Terraform "apply" role (admin), this one can
# only:
#   - upload new code to ONE Lambda function
#   - write files to ONE web bucket
#   - clear the cache of ONE CloudFront distribution
# ---------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

locals {
  # e.g. "repo:owner/name" or "repo:owner@123/name@456"
  subject_prefix = coalesce(var.github_subject_prefix, "repo:${var.github_repo}")
}

# Reuse the account's GitHub OIDC provider (created once, in "shared").
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# Who may assume the role: workflows on the main branch of this repo.
data "aws_iam_policy_document" "trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["${local.subject_prefix}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "deploy" {
  name               = var.name
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

# What the role may do (and nothing else).
data "aws_iam_policy_document" "deploy" {
  # Upload new API code and wait for the update to finish.
  statement {
    sid = "UpdateApiCode"
    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:GetFunction",
      "lambda:GetFunctionConfiguration",
    ]
    resources = [var.lambda_function_arn]
  }

  # Sync the Angular build into the web bucket.
  statement {
    sid       = "ListWebBucket"
    actions   = ["s3:ListBucket"]
    resources = [var.web_bucket_arn]
  }

  statement {
    sid       = "WriteWebFiles"
    actions   = ["s3:PutObject", "s3:DeleteObject", "s3:GetObject"]
    resources = ["${var.web_bucket_arn}/*"]
  }

  # Tell CloudFront to fetch the new files.
  statement {
    sid       = "InvalidateCache"
    actions   = ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"]
    resources = [var.distribution_arn]
  }
}

resource "aws_iam_role_policy" "deploy" {
  name   = "deploy-app"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy.json
}
