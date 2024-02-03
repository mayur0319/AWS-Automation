import boto3
import json
import calendar
import time
#session = boto3.Session(profile_name='prod')
#client = session.client('logs')
client = boto3.client('logs', region_name='us-east-2')
start_date_v2 = calendar.timegm(time.strptime('Oct 12, 2023 @ 00:00:00 UTC', '%b %d, %Y @ %H:%M:%S UTC'))
end_date_v2 = calendar.timegm(time.strptime('Oct 14, 2023 @ 23:59:59 UTC', '%b %d, %Y @ %H:%M:%S UTC'))
log_group_name = "" # Add the log group name
log_stream_name = "" # Add the log stream 
with open('logs_Oct_12-Oct_14.txt', 'w') as f:
    next_token = ""
    kwargs = {
        "logGroupName": log_group_name,
        "logStreamName": log_stream_name,
        "startTime": int(start_date_v2)*1000,
        "endTime": int(end_date_v2)*1000,
        "startFromHead": True
    }
    while True:
        if len(next_token) > 0:
            kwargs['nextToken'] = next_token
        response = client.get_log_events(**kwargs)
        if 'events' not in response.keys() or len(response['events']) == 0:
            break
        for event in response['events']:
            log_message = json.loads(event['message'])
            try:
                f.write(f"{log_message['message']}\n")
            except KeyError as e:
                continue
        if 'nextForwardToken' not in response.keys():
            break
        next_token = response['nextForwardToken']
