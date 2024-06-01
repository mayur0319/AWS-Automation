# sni-p01-util-instance-scheduler


## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_lambda_ec2_start_stop"></a> [lambda\_ec2\_start\_stop](#module\_lambda\_ec2\_start\_stop) | terraform-aws-modules/lambda/aws | 3.2.1 |

## Resources

| Name | Type |
|------|------|
| [aws_cloudwatch_event_rule.ec2_start_stop_rule](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_rule) | resource |
| [aws_cloudwatch_event_target.ec2_start_stop_target](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_event_target) | resource |
| [aws_cloudwatch_log_metric_filter.ec2_start_stop_log_filter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_metric_filter) | resource |
| [aws_cloudwatch_metric_alarm.ec2_start_stop_error](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_metric_alarm) | resource |
| [aws_iam_policy.lambda_ec2_start_stop_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.lambda_ec2_start_stop_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.ec2_start_stop_policy-attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.lambda-basic-execution-policy-attachment](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_lambda_permission.ec2_start_stop_lambda_permission](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_permission) | resource |
| [aws_sns_topic.ec2_start_stop_notification](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic) | resource |
| [aws_sns_topic_subscription.cloudwatch_alarms_subscription](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sns_topic_subscription) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.ec2_start_stop_assume_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.ec2_start_stop_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_account_tags"></a> [account\_tags](#input\_account\_tags) | Default tags | `map(string)` | n/a | yes |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | n/a | `any` | n/a | yes |
| <a name="input_emails_to_subscribe"></a> [emails\_to\_subscribe](#input\_emails\_to\_subscribe) | List of emailIds to subscribe for errors in key rotator lambda | `list(string)` | n/a | yes |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment | `string` | n/a | yes |
| <a name="input_exclude_account_list"></a> [exclude\_account\_list](#input\_exclude\_account\_list) | Exclude Accounts list | `list(string)` | <pre>[<br>  "905162661662",<br>  "655460373928",<br>  "633910205101",<br>  "075805711779",<br>  "125487031927",<br>  "463620995861",<br>  "075869202828",<br>  "799352561952"<br>]</pre> | no |
| <a name="input_layers"></a> [layers](#input\_layers) | List of layers for access key rotator lambda | `list(string)` | n/a | yes |
| <a name="input_runtime"></a> [runtime](#input\_runtime) | Lambda function runtime | `string` | `"python3.10"` | no |

## Outputs

No outputs.

## Lambda Unit Test
```
cd tests 
pip install -r requirements.txt
python -m coverage run -m unittest
python -m coverage report src/*.py
``` 
To get the coverage detailed HTML report on Local
```
python -m coverage html -d coverage_html src/*.py
```

## Deployed Infrastructure Test (Inspec)

### Insallation
Please follow the steps mentioned <a name="here"></a> [here](https://github.com/inspec/inspec) 

### Initialize
```
inspec init profile --platform aws infra-tests
```

### Writing tests
```
cd infra-tests/
```
Create new files with extention .rb

Follow the <a name="here"></a> [documentation](https://docs.chef.io/inspec/resources/)  for wirting the tests


### Execute
```
inspec exec lambda-test -t aws://
```

<!-- END_TF_DOCS -->