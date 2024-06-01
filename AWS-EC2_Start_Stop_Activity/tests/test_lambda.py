"""docstring
"""
import os
import unittest
from datetime import datetime
from moto import mock_ec2
import boto3
import coverage
from src.lambda_function import *


ec2 = boto3.client('ec2', region_name='us-east-2')
event = {}
os.environ['org_acct'] = "xxxxxxxx"
os.environ['exclude_acct'] = "xx, xx"


@mock_ec2()
class TestLambda(unittest.TestCase):
    """
    Unit Testing for Instance Scheduler Lambda 
    """

    # Test for get_tagged_instance_list function

    def test_e_get_tagged_instance_list(self):
        """
        Test if we get list of instances as empty
        """
        instance_list = get_tagged_instance_list(ec2)
        # self.assertEqual(instance_list, [])
        self.assertFalse(instance_list)

    def test_p_get_tagged_instance_list(self):
        """
        Test if we get list of instances as expected
        """
        ec2.run_instances(ImageId='ami-fake',
                          MinCount=1,
                          MaxCount=1,
                          InstanceType='t2.micro',
                          TagSpecifications=[{'ResourceType': 'instance',
                                              'Tags': [{'Key': 'Automate-Start-Stop',
                                                        'Value': '11:30-15:30'},
                                                       ]},
                                             ])

        response = ec2.describe_instances()["Reservations"]
        instanceid = response[0]['Instances'][0]['InstanceId']

        instance_list = get_tagged_instance_list(ec2)
        expected_result = [
            {'InstanceID': f'{instanceid}', 'Timing': '11:30-15:30'}]

        self.assertEqual(instance_list, expected_result)

    def test_n_get_tagged_instance_list(self):
        """
        Test if we do not get expected list of instance
        """
        ec2.run_instances(ImageId='ami-fake',
                          MinCount=1,
                          MaxCount=1,
                          InstanceType='t2.micro',
                          TagSpecifications=[{'ResourceType': 'instance',
                                              'Tags': [{'Key': 'Automate-Start',
                                                        'Value': '11:30-15:30'},
                                                       ]},
                                             ])

        instance_list = get_tagged_instance_list(ec2)
        false_result = [{'False': 'Condition'}]

        self.assertNotEqual(instance_list, false_result)
        self.assertEqual(instance_list, [])

    # Test for Time formate

    def test_p_time_format_check_start_stop_time(self):
        """
        Check if the Timing metioned in Tag value is formated correctly
        """
        test_instance_list = [{'InstanceID': 'i-start-no-space-ins',
                               'Timing': '11:30-15:30'},
                              {'InstanceID': 'i-start-with-space-ins',
                               'Timing': '  11 : 30 -  15 : 30   '},
                              {'InstanceID': 'i-stop-no-space-ins',
                               'Timing': '16:30-21:30'},
                              {'InstanceID': 'i-stop-with-spaces-ins',
                               'Timing': '  16  :  30 - 21 : 30 '},
                              {'InstanceID': 'i-stop-with-spaces--dif-format-ins',
                               'Timing': '  1:30 - 02 :30'}]
        current_time = datetime.strptime("12:30", "%H:%M").time()

        start_ec2, stop_ec2, skip_ec2 = check_start_stop_time(
            test_instance_list, current_time)

        regex_pattern = r"^\s*(?:[01]\d|2[0-3]|[0-9])\s*:\s*(?:[0-5][0-9]|[0-9])\s*-\s*(?:[01]\d|2[0-3]|[0-9])\s*:\s*(?:[0-5][0-9]|[0-9])\s*$"

        self.assertRegex(start_ec2[0].get('Timing'), regex_pattern)
        self.assertRegex(start_ec2[1].get('Timing'), regex_pattern)
        self.assertRegex(stop_ec2[0].get('Timing'), regex_pattern)
        self.assertRegex(stop_ec2[1].get('Timing'), regex_pattern)
        self.assertRegex(stop_ec2[2].get('Timing'), regex_pattern)

    def test_n_time_format_check_start_stop_time(self):
        """
        Check if the Timing metioned in Tag value is not correctly formatted
        """
        test_instance_list = [{'InstanceID': 'i-fakeinstance',
                               'Timing': '1220-1660'},
                              {'InstanceID': 'i-fakeec2id',
                               'Timing': '0130 0540'}]
        current_time = datetime.strptime("01:45", "%H:%M").time()

        start_ec2, stop_ec2, skip_ec2 = check_start_stop_time(
            test_instance_list, current_time)

        self.assertEqual(skip_ec2, test_instance_list)

    # Test for check_start_stop_time function

    def test_e_check_start_stop_time(self):
        """
        Check if we get empty list of instance
        """
        test_instance_list = []
        current_time = datetime.strptime("12:30", "%H:%M").time()

        start_ec2, stop_ec2, skip_ec2 = check_start_stop_time(
            test_instance_list, current_time)

        self.assertEqual(start_ec2, [])
        self.assertEqual(stop_ec2, [])

    def test_p_check_start_stop_time(self):
        """
        Check whether the current time falls under the timings tag value for the instances and get expected stop and start instances list.
        """
        test_instance_list = [{'InstanceID': 'i-start-no-space-ins',
                               'Timing': '11:30-15:30'},
                              {'InstanceID': 'i-start-with-space-ins',
                               'Timing': '  11 : 30 -  15 : 30   '},
                              {'InstanceID': 'i-stop-no-space-ins',
                               'Timing': '16:30-21:30'},
                              {'InstanceID': 'i-stop-no-space-ins',
                               'Timing': '  16  :  30 - 21 : 30 '}]
        current_time = datetime.strptime("12:30", "%H:%M").time()

        start_ec2, stop_ec2, skip_ec2 = check_start_stop_time(
            test_instance_list, current_time)

        expected_start_ec2 = [{'InstanceID': 'i-start-no-space-ins',
                               'Timing': '11:30-15:30'},
                              {'InstanceID': 'i-start-with-space-ins',
                               'Timing': '  11 : 30 -  15 : 30   '}]
        expected_stop_ec2 = [{'InstanceID': 'i-stop-no-space-ins',
                              'Timing': '16:30-21:30'},
                             {'InstanceID': 'i-stop-no-space-ins',
                              'Timing': '  16  :  30 - 21 : 30 '}]

        self.assertEqual(start_ec2, expected_start_ec2)
        self.assertEqual(stop_ec2, expected_stop_ec2)

    def test_n_check_start_stop_time(self):
        """
        Check that we do not get expected instances list
        """
        test_instance_list = [{'InstanceID': 'i-fakeinstance',
                               'Timing': '11:30-15:30'},
                              {'InstanceID': 'i-fakeec2id',
                               'Timing': '16:30-21:30'}]
        current_time = datetime.strptime("12:30", "%H:%M").time()

        start_ec2, stop_ec2, skip_ec2 = check_start_stop_time(
            test_instance_list, current_time)
        expected_start_ec2 = [{'InstanceID': 'False', 'Timing': 'Condition'}]
        expected_stop_ec2 = [{'InstanceID': 'False', 'Timing': 'Condition'}]

        self.assertNotEqual(start_ec2, expected_start_ec2)
        self.assertNotEqual(stop_ec2, expected_stop_ec2)

    # Test for instance_start_stop function

    def test_p_instance_start_stop(self):
        """
        Check if start and stop of instances is working in instance_start_stop function
        """
        ec2.run_instances(ImageId='ami-12345678',
                          InstanceType='t2.micro', MinCount=3, MaxCount=3)
        instance = ec2.describe_instances()
        inc1 = {'InstanceID': instance['Reservations']
                [0]['Instances'][0]['InstanceId']}
        inc2 = {'InstanceID': instance['Reservations']
                [0]['Instances'][1]['InstanceId']}
        inc3 = {'InstanceID': instance['Reservations']
                [0]['Instances'][2]['InstanceId']}

        instance_start_stop([inc1, inc2], [inc3], ec2)

        # Gets status of isnatnces
        response = ec2.describe_instance_status(
            InstanceIds=[
                inc1['InstanceID'],
                inc2['InstanceID'],
                inc3['InstanceID']])
        inc1_status = response['InstanceStatuses'][0]['InstanceState']['Name']
        inc2_status = response['InstanceStatuses'][1]['InstanceState']['Name']
        inc3_status = response['InstanceStatuses'][2]['InstanceState']['Name']

        self.assertEqual(inc1_status, "running")
        self.assertEqual(inc2_status, "running")
        self.assertEqual(inc3_status, "stopped")

    def test_n_instance_start_stop(self):
        """
        Check if start and stop of instances is working in instance_start_stop function
        """
        ec2.run_instances(ImageId='ami-12345678',
                          InstanceType='t2.micro', MinCount=3, MaxCount=3)
        instance = ec2.describe_instances()
        inc1 = {'InstanceID': instance['Reservations']
                [0]['Instances'][0]['InstanceId']}
        inc2 = {'InstanceID': instance['Reservations']
                [0]['Instances'][1]['InstanceId']}
        inc3 = {'InstanceID': instance['Reservations']
                [0]['Instances'][2]['InstanceId']}

        instance_start_stop([inc1, inc2], [inc3], ec2)

        # Gets status of instances
        response = ec2.describe_instance_status(
            InstanceIds=[
                inc1['InstanceID'],
                inc2['InstanceID'],
                inc3['InstanceID']])
        inc1_status = response['InstanceStatuses'][0]['InstanceState']['Name']
        inc2_status = response['InstanceStatuses'][1]['InstanceState']['Name']
        inc3_status = response['InstanceStatuses'][2]['InstanceState']['Name']

        self.assertNotEqual(inc1_status, "stooped")
        self.assertNotEqual(inc2_status, "stopped")
        self.assertNotEqual(inc3_status, "running")

    # Test for test_lambda_handler function

    # def test_lambda_handler(self):
    #     """
    #     Test the handler
    #     """
    #     self.assertTrue(lambda_handler(event, self))

if __name__ == '__main__':
    cov = coverage.Coverage()
    cov.start()

    try:
        unittest.main()
    except BaseException:  # catch-all except clause
        pass

    cov.stop()
    cov.save()

    cov.html_report(directory='covhtml')
    print("Done.")
