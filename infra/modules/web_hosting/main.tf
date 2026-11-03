# ---------------------------------------------------------------
# Module: web_hosting
# Serves the Angular app and the API from ONE CloudFront URL:
#
#   https://xxxx.cloudfront.net/          -> S3 bucket (Angular build)
#   https://xxxx.cloudfront.net/api/...   -> API Gateway -> Lambda
#
# Same origin for UI and API means no CORS setup in the browser.
# The S3 bucket stays private: only this CloudFront distribution
# can read it (Origin Access Control).
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
  s3_origin_id  = "web-bucket"
  api_origin_id = "api"
}

# ---------- Private bucket for the Angular build ----------

module "bucket" {
  source = "../s3_bucket"

  bucket_name   = var.bucket_name
  force_destroy = var.force_destroy

  # Let only this CloudFront distribution read files.
  extra_policy_documents = [data.aws_iam_policy_document.cloudfront_read.json]
}

data "aws_iam_policy_document" "cloudfront_read" {
  statement {
    sid       = "AllowCloudFrontRead"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${var.bucket_name}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.this.arn]
    }
  }
}

# CloudFront signs its S3 requests so the bucket can verify them.
resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = var.bucket_name
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ---------- Angular routing support ----------

# Angular handles URLs like /warehouses/42 in the browser, but S3 has
# no such file. This tiny function (runs at the CloudFront edge)
# serves index.html for any path without a file extension.
resource "aws_cloudfront_function" "spa_rewrite" {
  name    = "${var.name}-spa-rewrite"
  runtime = "cloudfront-js-2.0"
  publish = true
  comment = "Serve index.html for Angular routes"
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      // "/home" or "/" -> no "." in last segment -> Angular route
      var last = request.uri.split('/').pop();
      if (last.indexOf('.') === -1) {
        request.uri = '/index.html';
      }
      return request;
    }
  JS
}

# ---------- AWS-managed policies (looked up by name) ----------

# Cache static files at the edge (Angular file names change per build).
data "aws_cloudfront_cache_policy" "optimized" {
  name = "Managed-CachingOptimized"
}

# Never cache API responses.
data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

# Forward headers, cookies and query strings to the API (except Host,
# which must be API Gateway's own hostname).
data "aws_cloudfront_origin_request_policy" "all_except_host" {
  name = "Managed-AllViewerExceptHostHeader"
}

# Standard browser security headers (HSTS, X-Frame-Options, ...).
data "aws_cloudfront_response_headers_policy" "security" {
  name = "Managed-SecurityHeadersPolicy"
}

# ---------- The CloudFront distribution ----------

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  comment             = var.name
  default_root_object = "index.html"
  http_version        = "http2and3"

  # PriceClass_200 includes edge locations in India, but skips the
  # most expensive regions.
  price_class = "PriceClass_200"

  # Origin 1: the private S3 bucket.
  origin {
    origin_id                = local.s3_origin_id
    domain_name              = module.bucket.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  # Origin 2: the API Gateway HTTP API.
  origin {
    origin_id   = local.api_origin_id
    domain_name = var.api_domain

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # /api/* -> API (all methods, never cached).
  ordered_cache_behavior {
    path_pattern             = "/api/*"
    target_origin_id         = local.api_origin_id
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_except_host.id
    compress                 = true
  }

  # Everything else -> Angular files in S3.
  default_cache_behavior {
    target_origin_id           = local.s3_origin_id
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods            = ["GET", "HEAD"]
    cached_methods             = ["GET", "HEAD"]
    cache_policy_id            = data.aws_cloudfront_cache_policy.optimized.id
    response_headers_policy_id = data.aws_cloudfront_response_headers_policy.security.id
    compress                   = true

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_rewrite.arn
    }
  }

  # No country restrictions.
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Free default certificate for *.cloudfront.net.
  # A custom domain (bhandaran.ai) + ACM certificate comes at M14.
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
