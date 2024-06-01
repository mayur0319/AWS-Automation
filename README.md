# Automation Projects Repository

Welcome to the Automation Projects Repository! This repository contains various automation scripts and projects aimed at streamlining AWS management tasks within an organization. Below is an overview of the projects available in this repository:

## Access Key Rotation at Organization Level

### Description
This project automates the rotation of IAM access keys at scale within an AWS organization. It identifies all AWS account IDs within the organization and applies rotation measures uniformly using AWS Lambda, EventBridge, IAM, SES, SNS, and CloudWatch.

### Features
- Automated rotation of IAM access keys.
- Email notifications for key rotation actions.
- Customizable rotation periods and exclusion criteria.

### Prerequisites
- AWS Organizations configured and set up.
- Proper tagging of IAM users with email IDs.
- Configuration of SES for email notifications.

### Usage
- Configure environment variables.
- Deploy Lambda function and associated resources.
- Schedule EventBridge rules.

## EC2 Start/Stop at Organization Level

### Description
This project automates the start and stop actions of EC2 instances within an AWS organization. It helps optimize costs by ensuring instances are only running when necessary.

### Features
- Scheduled start and stop of EC2 instances.
- Customizable schedules based on organizational requirements.

### Prerequisites
- AWS Organizations configured and set up.
- Proper tagging of EC2 instances for scheduling.

### Usage
- Configure Lambda function and associated resources.
- Schedule Lambda execution using CloudWatch Events.

## Stale Resources Deletion

### Description
This project identifies and deletes stale resources within an AWS account, such as unattached EBS volumes, unused EIPs, and expired snapshots.

### Features
- Automated identification of stale resources.
- Customizable resource types and deletion criteria.

### Prerequisites
- Proper IAM permissions for resource deletion.

### Usage
- Configure Lambda function and associated resources.
- Customize resource types and deletion criteria.

## Additional Projects

In addition to the above projects, this repository may contain other automation scripts and projects aimed at improving operational efficiency, reducing costs, and enhancing security within an AWS environment.

## Contributing
Contributions to this repository are welcome! If you have suggestions, improvements, or new automation projects to add, please feel free to fork the repository and submit a pull request.

## Contact Information
For any questions, issues, or support, please contact [Your Contact Information].

