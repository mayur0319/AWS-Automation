module "lambda_sni-p01-util-instance-scheduler" {
  source                            = "terraform-aws-modules/lambda/aws"
  version                           = "3.2.1"
  function_name                     = "${var.resource_prefix}-lambda"
  create_role                       = false
  lambda_role                       = aws_iam_role.lambda_sni-p01-util-instance-scheduler-role.arn
  handler                           = "lambda_function.lambda_handler"
  runtime                           = var.runtime
  timeout                           = 900
  description                       = "Lambda function to Automate EC2 Start Stop keys"
  cloudwatch_logs_retention_in_days = 30
  cloudwatch_logs_tags              = var.account_tags
  source_path = [
     "../src"
  ]
  tags                              = var.account_tags

  environment_variables             = {
    org_acct                        = var.organization_account
    exclude_acct                    = join(",", var.exclude_account_list)
  }
  

  depends_on = [
    aws_iam_role_policy_attachment.lambda-basic-execution-policy-attachment
  ]
}

resource "aws_cloudwatch_event_rule" "sni-p01-util-instance-scheduler-rule" {
  name                = "${var.resource_prefix}-event-rule"
  description         = "Invokes lambda every 1 hour on weekdays (UTC)" 
  schedule_expression = "cron(0 * ? * 1-5 *)"
  # is_enabled          = true # Set this to true to start running the lambda
  state               = "ENABLED"
}

resource "aws_cloudwatch_event_target" "sni-p01-util-instance-scheduler-target" {
  rule      = aws_cloudwatch_event_rule.sni-p01-util-instance-scheduler-rule.name
  target_id = "${var.resource_prefix}"
  arn       = module.lambda_sni-p01-util-instance-scheduler.lambda_function_arn
}

resource "aws_lambda_permission" "sni-p01-util-instance-scheduler-lambda-permission" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_sni-p01-util-instance-scheduler.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sni-p01-util-instance-scheduler-rule.arn
}

resource "aws_cloudwatch_log_metric_filter" "sni-p01-util-instance-scheduler-log-filter" {
  name           = "${var.resource_prefix}-error-log-filter"
  log_group_name = module.lambda_sni-p01-util-instance-scheduler.lambda_cloudwatch_log_group_name
  pattern        = "ERROR"
  metric_transformation {
    name      = "${var.resource_prefix}-error-log-metric"
    namespace = "AWSPlatformAutomations"
    value     = "1"
  }
}
