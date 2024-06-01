# copyright: 2018, The Authors

title "sample section"

describe aws_iam_role('sni_p01_util_instance_scheduler_role') do
	it { should exist }
	its('role_name') { should eq 'sni_p01_util_instance_scheduler_role'}
	its('attached_policy_names') { should eq 'sni_p01_util_instance_scheduler_role' }
end
