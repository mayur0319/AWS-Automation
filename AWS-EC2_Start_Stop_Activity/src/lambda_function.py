"""_summary_

Returns:
	_type_: _description_
"""
from datetime import datetime, timezone
import os
from assume_role import assumed_role_session

def get_tagged_instance_list(ec2):
    """
    This funtion gets list of instances which has the 'Automate-Start-Stop' Tag attached to it.
    """
    custom_filter = [{
        'Name': 'tag:Automate-Start-Stop',
        'Values': ['*']
    }]

    # Get list of instances
    response = ec2.describe_instances(Filters=custom_filter)

    # Return Instance_ids and Timings
    instance_info = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            tags = instance.get('Tags')
            tag_value = None
            for tag in tags:
                if tag['Key'] == "Automate-Start-Stop":
                    tag_value = tag['Value']
                    break
            instance_info.append(
                {'InstanceID': instance_id, 'Timing': tag_value})

    return instance_info

def check_start_stop_time(instance_ids_list, current_time):
    """
    This funtions checks if the current time falls under the scheduled instance's time 
    """
    start_instances = []
    stop_instances = []
    skipped_instances = []

    for instance in instance_ids_list:
        try:
            start_time, stop_time = instance['Timing'].replace(
                " ", "").split("-")

            begin_time = datetime.strptime(start_time, "%H:%M").time()
            end_time = datetime.strptime(stop_time, "%H:%M").time()

            if current_time > begin_time and current_time < end_time:
                start_instances.append(instance)

            else:
                stop_instances.append(instance)

        except ValueError:
            print(
                f"Instance {instance['InstanceID']} has been skipped due to Tag value format error")
            skipped_instances.append(instance)

    return start_instances, stop_instances, skipped_instances


def instance_start_stop(start_instances, stop_instances, ec2):
    """
    This funtions will perform the start and stop of the isnatnces
    """
    start_instance_ids, stop_instance_ids = [], []

    # Start instances
    for instance_id in start_instances:
        start_instance_ids.append(instance_id['InstanceID'])

    if len(start_instance_ids) != 0:
        ec2.start_instances(InstanceIds=start_instance_ids)

    # Stop instances
    for instance_id in stop_instances:
        stop_instance_ids.append(instance_id['InstanceID'])
    if len(stop_instance_ids) != 0:
        ec2.stop_instances(InstanceIds=stop_instance_ids)


def get_filtered_account():
    """
    This fucntion fillters the account mentioned in env variable from the total org accounts list
    """
    org_root_acct_id = os.environ['org_acct']
    org_session = assumed_role_session(
        f"arn:aws:iam::{org_root_acct_id}:role/provisioning-admin")
    org = org_session.client('organizations')

    print("Filtering the accounts as per requirement")
    filtered_ids = []
    accounts = []
    next_token = None

    exclude_acct = os.environ['exclude_acct'].strip().split(",")

    # To get all the Accounts under organization
    while True:
        if next_token:
            response = org.list_accounts(NextToken=next_token)
        else:
            response = org.list_accounts()
        accounts.extend(response['Accounts'])
        next_token = response.get('NextToken')
        if not next_token:
            break

    # To get Account IDs of accounts.
    account_ids = []
    for account in accounts:
        account_ids.append(account['Id'])
    print(f'All accounts: {account_ids}\n')

    # Filter accounts
    for a_id in account_ids:
        if a_id not in exclude_acct:
            filtered_ids.append(id)
    return filtered_ids

def lambda_handler(event, context):
    """
    This is the main lambda functions to keep the instances active in the scheduked time   
    """
# Get Curernt UTC Time
    todays_day = datetime.now(timezone.utc).weekday()
# todays_day = 5
    current_time = datetime.now(timezone.utc).time()
    print(f"Current UTC Time {current_time} \n")

# Get Account IDs to which we will be performing
    filtered_acct_ids = get_filtered_account()

    # Check for Weekdays

    # filtered_acct_ids = ["587244064168"]
    print(f"Utility will be running on Accounts = {filtered_acct_ids} \n")

    if todays_day not in [5, 6]:
        # Loop into each account
        for account_id in filtered_acct_ids:

            try:
                session = assumed_role_session(
                    f"arn:aws:iam::{account_id}:role/provisioning-admin")
                ec2 = session.client('ec2', region_name="us-east-2")

                # Get Instance Details
                instance_ids_list = get_tagged_instance_list(ec2)

                start_instances, stop_instances, skipped_instances = check_start_stop_time(
                    instance_ids_list, current_time)

                instance_start_stop(start_instances, stop_instances, ec2)

                print(
                    f"\n-------------------------{account_id}-------------------------")
                print(f"Started Instances = {start_instances}")
                print(f"Stopped Instances = {stop_instances} \n")
                #If empty, will not print the following
                if skipped_instances:
                    print(
                        f"Skipped Instances due to Error = {skipped_instances} \n")

            except Exception as error:
                print(error)

    else:
        for account_id in filtered_acct_ids:
            try:
                session = assumed_role_session(
                    f"arn:aws:iam::{account_id}:role/provisioning-admin")
                ec2 = session.client('ec2', region_name="us-east-2")
                # ec2 = boto3.client('ec2')

                # Get Instance Details
                instance_ids_list = get_tagged_instance_list(ec2)

                instance_start_stop([], instance_ids_list, ec2)
                print(
                    f"\n-------------------------{account_id}-------------------------")
                print(f"Stopped Instances = {instance_ids_list} \n")

            except Exception as error:
                print(error)
                continue

# lambda_handler(a,b)
