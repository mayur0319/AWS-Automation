variable "aws_region" {
}

variable "environment" {
  type        = string
  description = "Environment"
}

variable "resource_prefix" {
  type        = string
  description = "Resource Prefix"
  default     = "sni-p01-util-instance-scheduler"
  
}

variable runtime {
  type        = string
  description = "Lambda function runtime"
  default     = "python3.10"
}

variable "account_tags" {
  type        = map(string)
  description = "Default tags"
}


variable "exclude_account_list" {
  type        = list(string)
  description = "Exclude Accounts list"
  default     = ["905162661662","655460373928","633910205101","075805711779","125487031927","463620995861","075869202828","799352561952"]
}

variable "organization_account" {
  type        = string
  description = "Organisation Account ID"
  default     = "075869202828"
}
