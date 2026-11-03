# ---------------------------------------------------------------
# Outputs of the cost_alarms module.
# ---------------------------------------------------------------

# SNS topic other alarms can reuse later (null if not created).
output "alerts_topic_arn" {
  description = "SNS topic for cost alerts"
  value       = try(aws_sns_topic.alerts[0].arn, null)
}
