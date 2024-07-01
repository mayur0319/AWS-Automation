variable "aws_region" {
}

variable "environment" {
  type        = string
  description = "Environment"
}

variable "resource_prefix" {
  type        = string
  description = "Resource Prefix"
  default     = ""
  
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
  default     = []
}

variable "organization_account" {
  type        = string
  description = "Organisation Account ID"
  default     = ""
}
