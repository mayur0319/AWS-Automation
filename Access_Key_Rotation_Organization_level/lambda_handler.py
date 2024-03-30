'''

IAM Key rotator Lambda
 - Solution to rotate AWS IAM Access key in 90 days for all accounts in the organization.
 
Pre-requisites
 - To run full functionality each IAM user should have a tag: Email ID with proper email ID. (case insensitive)
 - The below environment variable must be configured with the given value before running the functionality.
    - limit_days = 90
    - notice_period = 15
    - max_users =200
    - Clean_up = True or False
    - SENDER_EMAIL = <Email that will be used to notify user>
 - To run the initial clean-up only, set Clean_up = True

'''
import json
import boto3
from datetime import datetime
from datetime import date
from datetime import timedelta
from botocore.exceptions import ClientError
import pyminizip
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import re
import string
import random
from assume_role import *

ses = boto3.client('ses')
pattern = r"^[a-zA-Z0-9_.+-]+@smith-nephew.com"
SENDER = os.environ['SENDER_EMAIL']

def lambda_handler(event, context):
    org_root_acct_id = ""
    org_session = assumed_role_session("arn:aws:iam::{}:role/provisioning-admin".format(org_root_acct_id))
    org = org_session.client('organizations')
    # Array to store all account information.
    accounts = []
    next_token = None
    Clean_up = os.environ['Clean_up']
    # Array to store account IDs of required accounts.
    exclude_acct = os.environ['exclude_acct'].strip().split(",")
    table = "<table><tr><th>Account number</th><th>user_name</th><th>Access key ID</th><th>Action</th></tr>"

    while True:
        if next_token:
            response = org.list_accounts(NextToken=next_token)
        else:
            response = org.list_accounts()
        accounts.extend(response['Accounts'])
        next_token = response.get('NextToken')
        if not next_token:
            break

    # Array to store IDs of accounts.
    account_ids = []
    for account in accounts:
        account_ids.append(account['Id'])
    print(account_ids)
    # filtered_acct_ids will store the account IDs of required accounts.
    filtered_acct_ids = filtered_account(account_ids, exclude_acct)
    max_users = int(os.environ['max_users'])  # No pagination used as there are only ~125 users currently
    limit_days = int(os.environ['limit_days']) # Number of days to notify user about deactivation
    notice_period = int(os.environ['notice_period'])  # Key will be deactivated 10 days after user notification
    today = date.today()
    user_type_tag = "TYPE"
    for account_id in filtered_acct_ids:
        print(account_id)
        try:
            session = assumed_role_session("arn:aws:iam::{}:role/provisioning-admin".format(account_id))

            iam = session.client('iam')
            user_list = iam.list_users(MaxItems=max_users)
            for user in user_list["Users"]:

                # Initialize empty variables
                user_details = ""
                EmailID = ""
                EXEMPT= ""
                user_type = ""
                deactivate_on = ""
                delete_on = ""
                user_name = user["UserName"]
                user_details = iam.get_user(UserName=user_name)
                print("..........................................................")
                print("Inside user "+ user_name)
            
                # Parse tags
                if "Tags" in user_details["User"]:
                    for tag in user_details["User"]["Tags"]:  # previous for tag in user_details["User"]["Tags"]:
                        # Get user type
                        if tag["Key"].strip().upper() == user_type_tag:
                            user_type = tag["Value"].strip().upper()
                        if tag["Key"].strip().upper() == "DEACTIVATE_ON":
                            deactivate_on = tag["Value"]
                        if tag["Key"].strip().upper() == "DELETE_ON":
                            delete_on = tag["Value"]
                        if tag["Key"].strip().upper() == "EMAILID":
                            EmailID = tag["Value"]
                        if tag["Key"].strip().upper() == "EXEMPT":
                            EXEMPT = tag["Value"]

                if EXEMPT =="True":
                    print("[INFO] Exempt tag found, no action required")
                    continue
                if Clean_up == "True":
                    result = initial_cleanup(iam, user_name, limit_days, EmailID, account_id, table)
                    print("[INFO] Initial cleanup successful")
                    final_table = result + "</table>"
                    body = "We have noticed that initial cleanup activity get performed on some of the AWS accounts. \r\nKeys which are deleted and disabled are as follows. \r\n" + final_table
                    html_body = "We have noticed that initial cleanup activity get performed on some of the AWS accounts. <br>Keys which are deleted and disabled are as follows. <br>" + final_table
                    notify_AWS_Team(body, html_body)
                    continue
                
                print("EMAILID :- "+ EmailID)
                print(validate_email(EmailID))
                if validate_email(EmailID):
                    # List access keys
                    key_id_response = iam.list_access_keys(UserName=user_name)
                    key_id_count = len(key_id_response["AccessKeyMetadata"])
                    
                    if key_id_count == 2:
                        print("key_id_response")
                        print(key_id_response["AccessKeyMetadata"])
                        # Get each key details
                        key0 = key_id_response["AccessKeyMetadata"][0]
                        delta0 = (today - key0["CreateDate"].date()).days
                        response_0 = iam.get_access_key_last_used(AccessKeyId= key0["AccessKeyId"])
                        Last_Used_0 = response_0["AccessKeyLastUsed"]
                        if Last_Used_0.get("LastUsedDate"):
                            Last_Used_date_0 = (today - Last_Used_0["LastUsedDate"].date()).days
                        else:
                            Last_Used_date_0 = None
                        
                        key1 = key_id_response["AccessKeyMetadata"][1]
                        delta1 = (today - key1["CreateDate"].date()).days
                        response_1 = iam.get_access_key_last_used(AccessKeyId= key1["AccessKeyId"])
                        Last_Used_1 = response_1["AccessKeyLastUsed"] 
                        if Last_Used_1.get("LastUsedDate"):
                            Last_Used_date_1 = (today - Last_Used_1["LastUsedDate"].date()).days
                        else:
                            Last_Used_date_1 = None
                        
                        if delta0 >= limit_days or delta1 >= limit_days:     
                            print("[INFO] 2 Keys (" + str(delta0) + " days, " + str(delta1) + " days) exist for the user " + user_name)
                            # Find key to expire and the key to keep
                            key_expiring = key0
                            key_keep = key1
                            if delta1 > delta0:
                                key_expiring = key1
                                key_keep = key0
                            
                            # check for keys ready to get deactivated
                            if deactivate_on == str(date.today()):
                                deactivate_key(iam, user_name, key_expiring["AccessKeyId"])
                                body = "Please be informed that your AWS IAM Access key '" + key_expiring["AccessKeyId"][:16] + "****' has been deactivated. As part of IAM Access key rotation, it will be deleted in " + str(notice_period) + " days."
                                notify_user(user_name, EmailID, body, body)
                                unset_user_tag(iam, user_name, "deactivate_on")
                                set_user_tag(iam, user_name, "delete_on", str(today + timedelta(days=notice_period)))
                            # check for keys ready to get deleted
                            if delete_on == str(date.today()):
                                delete_key(iam, user_name, key_expiring["AccessKeyId"])
                                body = "Please be informed that your AWS IAM Access key '" + key_expiring["AccessKeyId"][:16] + "****' has been deleted as part of IAM Access key rotation."
                                notify_user(user_name, EmailID, body, body)
                                unset_user_tag(iam, user_name, "delete_on")
                            # If No key is scheduled to get deactivated
                            # This condition is to cleanup users who are currently having 2 keys
                            if deactivate_on == "" and delete_on == "":
                                #check for last key used
                                if (Last_Used_date_0 is None or Last_Used_date_0 >= limit_days) or (delta1 >= limit_days and (Last_Used_date_1 is None or Last_Used_date_1 >= limit_days)):
                                    if Last_Used_date_0 is None or Last_Used_date_0 >= limit_days:
                                        print("[INFO] Deleting key which is not used form " + str(limit_days) + " days for user " + user_name)
                                        delete_key(iam, user_name, key_expiring["AccessKeyId"])
                                    if delta1 >= limit_days and (Last_Used_date_1 is None or Last_Used_date_1 >= limit_days):
                                        print("[INFO] Deleting key which is not used form " + str(limit_days) + " days for user " + user_name)
                                        delete_key(iam, user_name, key_keep["AccessKeyId"])
                                elif key_expiring["Status"] == "Inactive":
                                    # Any existing inactive keys older than 80 days will be deleted.
                                    delete_key(iam, user_name, key_expiring["AccessKeyId"])
                                    print("[INFO] Deleted Inactive key older than " + str(limit_days) + " days for user " + user_name)
                                    # Create new key
                                    new_key_response = create_new_key(user_name, iam)
                                    # Generate random file password for encryption. 
                                    rand_pw = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
                                    body = "Your AWS IAM Access Key '" + key_expiring["AccessKeyId"][:16] + "****' has been Expired and Inactive. As part of IAM Access key rotation, it was deleted.\r\nNew IAM access keys are created for you and will be shared in a separate email.\r\nPassword to open the file : " + str(rand_pw)
                                    html_body = "Your AWS IAM Access Key '" + key_expiring["AccessKeyId"][:16] + "****' has been Expired and Inactive. As part of IAM Access key rotation, it will be deleted.<br>Password to open the file : " + str(rand_pw)
                                    # Inform and share zip password
                                    notify_user(user_name, EmailID, body, html_body)
                                    # Send credentials
                                    notify_user_attach(user_name, EmailID, new_key_response["AccessKey"]["AccessKeyId"], new_key_response["AccessKey"]["SecretAccessKey"], str(rand_pw))
                                    
                                elif key_expiring["Status"] == "Active" and key_keep["Status"] == "Inactive":
                                    # Younger key is Inactive. Hence delete the inactive key and create a new key.
                                    delete_key(iam, user_name, key_keep["AccessKeyId"])
                                    print("[INFO] Deleted Inactive key in-order to create a new key for key rotation for user " + user_name)
                                    # Create new key
                                    new_key_response = create_new_key(user_name, iam)
                                    # Generate random file password for encryption. 
                                    rand_pw = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
                                    body = "Your AWS IAM Access Key '" + key_expiring["AccessKeyId"][:16] + "****' is nearing its expiry. As part of IAM Access key rotation, it will be deactivated in " + str(notice_period) + " days.\r\nNew IAM access keys are created for you and will be shared in a separate email.\r\nPassword to open the file : " + str(rand_pw)
                                    html_body = "Your AWS IAM Access Key '" + key_expiring["AccessKeyId"][:16] + "****' is nearing its expiry. As part of IAM Access key rotation, it will be deactivated in " + str(notice_period) + " days.<br>New IAM access keys are created for you and will be shared in a separate email.<br>Password to open the file : " + str(rand_pw)
                                    # Inform and share zip password
                                    notify_user(user_name, EmailID, body, html_body)
                                    # Send credentials
                                    notify_user_attach(user_name, EmailID, new_key_response["AccessKey"]["AccessKeyId"], new_key_response["AccessKey"]["SecretAccessKey"], str(rand_pw))
                                    set_user_tag(iam, user_name, "deactivate_on", str(today + timedelta(days=notice_period)))
                                elif key_expiring["Status"] == "Active" and key_keep["Status"] == "Active":
                                    # 2 Active keys => Deactivate the older key
                                    body = "We have noticed that your AWS IAM user currently has 2 active Access Keys. The key " + key_expiring["AccessKeyId"][:16] + "**** is nearing its expiry.\r\nAs part of IAM Access Key rotation, it will be deactivated in " + str(notice_period) + " days. Please use the other existing key to continue accessing AWS resources."
                                    html_body = "We have noticed that your AWS IAM user currently has 2 active Access Keys. The key " + key_expiring["AccessKeyId"][:16] + "**** is nearing its expiry.<br>As part of IAM Access Key rotation, it will be deactivated in " + str(notice_period) + " days. Please use the other existing key to continue accessing AWS resources."
                                    notify_user(user_name, EmailID, body, html_body)
                                    set_user_tag(iam, user_name, "deactivate_on", str(today + timedelta(days=notice_period)))
                        
                    elif key_id_count == 1:        

                        key = key_id_response["AccessKeyMetadata"][0]
                        delta = (today - key["CreateDate"].date()).days
                        response = iam.get_access_key_last_used(AccessKeyId= key["AccessKeyId"])
                        Last_Used = response["AccessKeyLastUsed"]
                        if Last_Used.get("LastUsedDate"):
                            Last_Used_date = (today - Last_Used["LastUsedDate"].date()).days
                        else:
                            Last_Used_date = None

                        # Check if key is nearing expiry
                        if delta >= limit_days:
                            print("[INFO] 1 Key (" + str(delta) + " days) exist exist for the user " + user_name)
                            #check for last key used
                            if Last_Used_date is None or Last_Used_date >= limit_days:
                                print("[INFO] Deleted key which is not used form " + str(limit_days) + " days for user " + user_name)
                                delete_key(iam, user_name, key["AccessKeyId"])
                            elif key["Status"] == "Active":
                                # Issue new key if the active key is about to expire
                                print("[DEBUG] Key is Active. Issue new key for the user " + user_name)
                                new_key_response = create_new_key(user_name, iam)
                                # Generate random file password for encryption. 
                                rand_pw = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
                                body = "Your AWS IAM Access Key '" + key["AccessKeyId"][:16] + "****' is nearing its expiry. As part of IAM Access key rotation, it will be deactivated in " + str(notice_period) + " days.\r\nNew IAM access keys are created for you and will be shared in a separate email.\r\nPassword to open the file : " + str(rand_pw)
                                html_body = "Your AWS IAM Access Key '" + key["AccessKeyId"][:16] + "****' is nearing its expiry. As part of IAM Access key rotation, it will be deactivated in " + str(notice_period) + " days.<br>New IAM access keys are created for you and will be shared in a separate email.<br>Password to open the file : " + str(rand_pw)
                                # Inform and share zip password
                                notify_user(user_name, EmailID, body, html_body)
                                notify_user_attach(user_name, EmailID, new_key_response["AccessKey"]["AccessKeyId"], new_key_response["AccessKey"]["SecretAccessKey"], str(rand_pw))
                                set_user_tag(iam, user_name, "deactivate_on", str(today + timedelta(days=notice_period)))
                            elif key["Status"] == "Inactive":
                                # Remove inactive keys if they are more than 80 days old
                                # No notification sent for removing existing inactive key that is more than 80 days
                                print("[INFO] Key is In-active. Deleting Inactive key that is more than " + str(limit_days + notice_period) + " days old for user " + user_name)
                                delete_key(iam, user_name, key["AccessKeyId"])

                else:
                    print("[INFO] Email id is not present in proper format for the user " + user_name)
        except:
            print("[Error] Not able to access the new account.")
            body= "We have noticed that new account "+account_id+" has been added into the organization and which does not have provisioning admin role.\r\nTo exclude that account please add it into the exclude_acct list."
            html_body= "We have noticed that new account "+account_id+" has been added into the organization and which does not have provisioning admin role.<br>To exclude that account please add it into the exclude_acct list."
            notify_AWS_Team(body, html_body)
    return {
        'statusCode': 200,
        'body': json.dumps('Execution Completed.')
    }
    
def filtered_account(account_ids, exclude_acct):
    print("[INFO] Filter the accounts as per requirement")
    filtered_ids = []
    for id in account_ids:
        if id not in exclude_acct:
          filtered_ids.append(id)
    return filtered_ids

def create_new_key(user_name, iam):
    print("[INFO] Create and return new key and secrets for user " + user_name)
    key_response = iam.create_access_key(UserName=user_name)
    # Do not log secret key
    return key_response
    
def notify_user(user_name, recipient, body, html_body):
    print("[INFO] Sending email to " + user_name + " ( " + recipient + " ) using ses ")
    CcAddresses =""
    CONFIGURATION_SET = ""
    SUBJECT = "Attention - AWS Access Key Expiry notification"
    body = "Hi " + user_name + ",\r\n\r\n" + body + "\r\n\r\nPlease contact , if you have any concerns.\r\n\r\nThanks, \r\nAWS Platform Automation"
    html_body = "Hi " + user_name + ",<br><br>" + html_body + "<br><br>Please contact <a href='mailto:Aws-Cloud-Platform@smith-nephew.com'></a>, if you have any concerns.<br><br>Thanks, <br>AWS Platform Automation's "
    BODY_TEXT = (body)
    BODY_HTML = "<html><head></head><body><p>" + html_body + "</p></body></html>"
    CHARSET = "UTF-8"
    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT 
    msg['From'] = SENDER 
    msg['To'] = recipient
    msg['Importance'] = 'High'
    msg['Cc'] = CcAddresses
    
    # Encode the text and HTML content and set the character encoding. This step is necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')
    
    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)
    
    # Attach the multipart/alternative child container to the multipart/mixed parent container.
    msg.attach(msg_body)
    
    try:
        #Provide the contents of the email.
        response = ses.send_raw_email(
            Source=SENDER,
            Destinations=[
                recipient,
                CcAddresses
                ],
            RawMessage={
                'Data':msg.as_string(),
            },
            # Optional configurationSet
            ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
        print("[ERROR] Something went wrong while sending SES notification to " + recipient + " for user " + user_name)
    else:
        print("[INFO] Email sent, Message ID:" + response['MessageId'] + " to user " + user_name)
    return

def notify_AWS_Team(body, html_body):
    print("[INFO] Sending email to AWS team using ses ")
    CONFIGURATION_SET = ""
    recipient = ""
    SUBJECT = "Attention - New Account Found."
    body = "Hi AWS Team,\r\n\r\n" + body +"\r\n\r\nThanks"
    html_body = "Hi AWS Team,<br><br>" + html_body +"<br><br>Thanks"
    BODY_TEXT = (body)
    BODY_HTML = "<html><head></head><body><p>" + html_body + "</p></body></html>"
    CHARSET = "UTF-8"
    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT 
    msg['From'] = SENDER 
    msg['To'] = recipient
    msg['Importance'] = 'High'
    
    # Encode the text and HTML content and set the character encoding. This step is necessary if you send a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')
    
    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)
    
    # Attach the multipart/alternative child container to the multipart/mixed parent container.
    msg.attach(msg_body)
    
    try:
        #Provide the contents of the email.
        response = ses.send_raw_email(
            Source=SENDER,
            Destinations=[
                recipient,
                ],
            RawMessage={
                'Data':msg.as_string(),
            },
            # Optional configuration set
            ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
        print("[ERROR] Something went wrong while sending SES notification to " + recipient + " for user " + user_name)
    else:
        print("[INFO] Email sent to the AWS Team")
    return   

def notify_user_attach(user_name, recipient, access_key, access_secret, rand_password):
    # Prepare attachment
    f = open("/tmp/" + user_name + ".txt", "w")
    f.write("Access Key Id : " + access_key + "\nSecret Access Key : " + access_secret )
    f.close()
    # Zip file with password
    pyminizip.compress( "/tmp/" +user_name + ".txt", "", "/tmp/" +user_name + ".zip", rand_password, 0)    
    ATTACHMENT = "/tmp/" +user_name + ".zip"
    
    print("[INFO] Sending email to " + user_name + " ( " + recipient + " ) with attachment using ses ")
    # SENDER =
    CONFIGURATION_SET = ""
    AWS_REGION = "us-east-2"
    #REPLY_ADDRESS = ""
    SUBJECT = "Attention - New AWS access and Secret access key for the expired key"
    body = "Hi " + user_name + ",\r\n\r\nNew AWS IAM Access keys are created for you. Please find the attachment. The password to open the file is shared in a separate email.\r\n\r\nPlease contact .com, if you have any concerns.\r\n\r\nThanks, \r\nAWS Platform Automation"
    html_body = "Hi " + user_name + ",<br><br>New AWS IAM Access keys are created for you. Please find the attachment. The password to open the file is shared in a separate email.<br><br>Please contact <a href='mailto:'>Aws-Cloud-Platform@smith-nephew.com</a>, if you have any concerns.<br><br>Thanks, <br>AWS Platform Automation"
    BODY_TEXT = (body)
    BODY_HTML = "<html><head></head><body><p>" + html_body + "</p></body></html>"
    CHARSET = "UTF-8"
    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT 
    msg['From'] = SENDER 
    msg['To'] = recipient
    msg['Importance'] = 'High'

    # Encode the text and HTML content and set the character encoding. This step is necessary if you're sending a message with characters outside the ASCII range.
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')
    
    # Add the text and HTML parts to the child container.
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)
    
    # Define the attachment part and encode it using MIMEApplication.
    att = MIMEApplication(open(ATTACHMENT, 'rb').read())

    # Add a header to tell the email client to treat this part as an attachment, and to give the attachment a name.
    att.add_header('Content-Disposition','attachment',filename=os.path.basename(ATTACHMENT))

    # Attach the multipart/alternative child container to the multipart/mixed parent container.
    msg.attach(msg_body)

    # Add the attachment to the parent container.
    msg.attach(att)
    
    # Remove the file
    os.remove("/tmp/" +user_name + ".txt")
    os.remove("/tmp/" +user_name + ".zip")
    try:
        #Provide the contents of the email.
        response = ses.send_raw_email(
            Source=SENDER,
            Destinations=[
                recipient,
            ],

            RawMessage={
                'Data':msg.as_string(),
            },
            # ReplyToAddresses=[REPLY_ADDRESS], # Not supported
            ConfigurationSetName=CONFIGURATION_SET
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
        print("[ERROR] Something went wrong while sending SES notification with attachment to " + recipient + " for user " + user_name)
    else:
        print("[INFO] Email sent with attachment, Message ID:" + response['MessageId'] + " to user " + user_name)
    return

def set_user_tag(iam, user_name, tag_key, tag_value):
    print("[INFO] Setting tag " + tag_key + " = " + tag_value  + " for user " + user_name)
    tag_response = iam.tag_user(UserName=user_name,Tags=[{'Key': tag_key, 'Value': tag_value}])
    if tag_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("[ERROR] Something went wrong while adding tag " + tag_key + " = " + tag_value + " for user " + user_name)
    return
    
def unset_user_tag(iam, user_name, tag_key):
    print("[INFO] Removing tag " + tag_key + " for user " + user_name)
    tag_response = iam.untag_user(UserName=user_name,TagKeys=[tag_key])
    if tag_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("[ERROR] Something went wrong while removing tag " + tag_key + " for user " + user_name)
    return
    
def deactivate_key(iam, user_name, key_expiring_id):
    # deactivate IAM access key
    print("[INFO] Deactivating key " + key_expiring_id[:16] + "**** for user " + user_name)
    deactivate_response = iam.update_access_key(UserName=user_name, AccessKeyId=key_expiring_id, Status="Inactive")
    if deactivate_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("[ERROR] Something went wrong while deactivating key " + key_expiring_id[:16] + "**** for user " + user_name)
    return
    
def delete_key(iam, user_name, key_expiring_id):
    # delete IAM access key
    print("[INFO] Deleting key " + key_expiring_id[:16] + "**** for user " + user_name)
    delete_response = iam.delete_access_key(UserName=user_name, AccessKeyId=key_expiring_id)
    if delete_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("[ERROR] Something went wrong while deleting key " + key_expiring_id[:16] + "**** for user " + user_name)
    return

def initial_cleanup(iam, user_name, limit_days, EmailID, account_id, table):
    key_id_response = iam.list_access_keys(UserName=user_name)
    key_id_count = len(key_id_response["AccessKeyMetadata"])
    today = date.today()

    if key_id_count == 2:
        # Get each key details
        key0 = key_id_response["AccessKeyMetadata"][0]
        delta0 = (today - key0["CreateDate"].date()).days
        
        key1 = key_id_response["AccessKeyMetadata"][1]
        delta1 = (today - key1["CreateDate"].date()).days            
        
        if delta0 >= limit_days or delta1 >= limit_days:     
            print("[INFO] 2 Keys (" + str(delta0) + " days, " + str(delta1) + " days) exist for the user " + user_name)
            # Find key to expire and the key to keep
            key_expiring = key0
            key_keep = key1
            if delta1 > delta0:
                key_expiring = key1
                key_keep = key0
            
            if key_expiring["Status"] == "Inactive" and key_keep["Status"] == "Inactive":
                # Any existing inactive keys older than 80 days will be deleted.
                if (today - key_keep["CreateDate"].date()).days >= limit_days:
                    delete_key(iam, user_name, key_keep["AccessKeyId"])
                    table = table + "<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_keep["AccessKeyId"]+"</td><td>Delete</td></tr>"
                delete_key(iam, user_name, key_expiring["AccessKeyId"])
                print("[INFO] Deleted Inactive key older than " + str(limit_days) + " days for user " + user_name)
                table = table + "<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_expiring["AccessKeyId"]+"</td><td>Delete</td></tr>"
            elif key_expiring["Status"] == "Inactive":
                # Any existing inactive keys older than 80 days will be deleted.
                delete_key(iam, user_name, key_expiring["AccessKeyId"])
                table = table + "<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_expiring["AccessKeyId"]+"</td><td>Delete</td></tr>"
                print("[INFO] Deleted Inactive key older than " + str(limit_days) + " days for user " + user_name)
            elif key_expiring["Status"] == "Active" and key_keep["Status"] == "Inactive" and (today - key_keep["CreateDate"].date()).days >= limit_days:
                # Any existing inactive keys older than 80 days will be deleted.
                delete_key(iam, user_name, key_keep["AccessKeyId"])
                table = table + "<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_keep["AccessKeyId"]+"</td><td>Delete</td></tr>"
                print("[INFO] Deleted Inactive key older than " + str(limit_days) + " days for user " + user_name)
                
    elif key_id_count == 1:        
                
        key = key_id_response["AccessKeyMetadata"][0]
        delta = (today - key["CreateDate"].date()).days
        # Check if key is nearing expiry
        if delta >= limit_days:
            print("[INFO] 1 Key (" + str(delta) + " days) exist exist for the user " + user_name)
            if key["Status"] == "Inactive":
               # Remove inactive keys if they are more than 80 days old
               # No notification sent for removing existing inactive key that is more than 80 days
               table = table + "<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key["AccessKeyId"]+"</td><td>Delete</td></tr>"
               print("[INFO] Key is In-active. Deleting Inactive key that is more than " + str(limit_days) + " days old for user " + user_name)
               delete_key(iam, user_name, key["AccessKeyId"])
               
    if EmailID == "" or EmailID.strip() == "":
        table = For_emailId_not_present(iam, user_name, limit_days, account_id)
    return table

def For_emailId_not_present(iam, user_name, limit_days, account_id, table):
    print("[ERROR] EmailId not defined for user " + user_name)
    key_id_response = iam.list_access_keys(UserName=user_name)
    key_id_count = len(key_id_response["AccessKeyMetadata"])
    today = date.today()
    if key_id_count == 2:
        # Get each key details
        key0 = key_id_response["AccessKeyMetadata"][0]
        delta0 = (today - key0["CreateDate"].date()).days
        
        key1 = key_id_response["AccessKeyMetadata"][1]
        delta1 = (today - key1["CreateDate"].date()).days
        
        if delta0 >= limit_days or delta1 >= limit_days:     
            print("[INFO] 2 Keys (" + str(delta0) + " days, " + str(delta1) + " days) exist for the user " + user_name)
            # Find key to expire and the key to keep
            key_expiring = key0
            key_keep = key1
            if delta1 > delta0:
                key_expiring = key1
                key_keep = key0
            if key_expiring["Status"] == "Active" and key_keep["Status"] == "Active":
                if (today - key_keep["CreateDate"].date()).days >= limit_days:
                    deactivate_key(iam, user_name, key_keep["AccessKeyId"])
                    table = table +"<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_keep["AccessKeyId"]+"</td><td>Deactivate</td></tr>"
                deactivate_key(iam, user_name, key_expiring["AccessKeyId"])
                table = table +"<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_expiring["AccessKeyId"]+"</td><td>Deactivate</td></tr>"
            elif key_expiring["Status"] == "Active":
                deactivate_key(iam, user_name, key_expiring["AccessKeyId"])
                table = table +"<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_expiring["AccessKeyId"]+"</td><td>Deactivate</td></tr>"
            elif key_expiring["Status"] == "Inactive" and key_keep["Status"] == "Active" and (today - key_keep["CreateDate"].date()).days >= limit_days:
                    deactivate_key(iam, user_name, key_keep["AccessKeyId"])
                    table = table +"<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key_keep["AccessKeyId"]+"</td><td>Deactivate</td></tr>"
    
    if key_id_count == 1:
        key = key_id_response["AccessKeyMetadata"][0]
        delta = (today - key["CreateDate"].date()).days
        if delta >= limit_days:
           if key["Status"] == "Active":
                deactivate_key(iam, user_name, key["AccessKeyId"])
                table = table +"<tr><td>"+account_id+"</td><td>"+user_name+"</td><td>"+key["AccessKeyId"]+"</td><td>Deactivate</td></tr>"
    return table

def validate_email(EmailID):
    if re.match(pattern, EmailID):
        return True
    else:
        return False
    