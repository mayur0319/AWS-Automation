resource "aws_iam_role" "lambda_sni-p01-util-instance-scheduler-role" {
  name               = "${var.resource_prefix}-role"
  description        = "Role for ${var.resource_prefix} Lambda Function"
  assume_role_policy = data.aws_iam_policy_document.sni-p01-util-instance-scheduler-assume-policy.json
  tags               = var.account_tags
}

resource "aws_iam_policy" "lambda_sni-p01-util-instance-scheduler-policy" {
  name        = "${var.resource_prefix}-policy"
  path        = "/"
  description = "Policy for ${var.resource_prefix} Lambda Function"
  policy      = data.aws_iam_policy_document.sni-p01-util-instance-scheduler-policy.json
  tags        = var.account_tags
}

resource "aws_iam_role_policy_attachment" "sni-p01-util-instance-scheduler-policy-attachment" {
  role       = aws_iam_role.lambda_sni-p01-util-instance-scheduler-role.name
  policy_arn = aws_iam_policy.lambda_sni-p01-util-instance-scheduler-policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda-basic-execution-policy-attachment" {
  role       = aws_iam_role.lambda_sni-p01-util-instance-scheduler-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
