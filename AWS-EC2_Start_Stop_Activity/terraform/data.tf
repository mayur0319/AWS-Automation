data "aws_region" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "sni-p01-util-instance-scheduler-policy" {
  statement {
    sid = "AllowEC2Permissions"
    actions = [
      "ec2:Describe*",
      "ec2:List*",
      "ec2:Get*",
      "ec2:StartInstances",
      "ec2:StopInstances"
    ]
    resources = ["*"]
  }
  
  statement {
    sid = "AllowSTS"
    actions = ["sts:AssumeRole"]
    resources = ["*"]       
  }
}

data "aws_iam_policy_document" "sni-p01-util-instance-scheduler-assume-policy" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = [
      "sts:AssumeRole",
    ]
  }
}
