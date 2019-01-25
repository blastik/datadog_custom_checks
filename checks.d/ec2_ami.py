import sys
from datetime import datetime
import time

# the following try/except block will make the custom check compatible with any Agent version
try:
    from checks import AgentCheck
except ImportError:
    from datadog_checks.checks import AgentCheck

try:
    import boto3
except ImportError:
    sys.exit(''''boto3 module is necessary to run this check
             See https://docs.datadoghq.com/agent/faq/custom_python_package/ for more info''')

# content of the special variable __version__ will be shown in the Agent status page
__version__ = "1.0.0"


class AMICheck(AgentCheck):

    STATUS_ABSENT = 'absent'
    STATUS_PRESENT = 'present'

    def ami_exists(self, aws_region, ami_name):
        try:
            client = boto3.client('ec2', region_name=aws_region)
            response = client.describe_images(Filters=[
                {
                    'Name': 'name',
                    'Values': [ami_name]
                }
            ]
            )
            if not response['Images']:
                return self.STATUS_ABSENT, []
            else:
                all = response['Images']
                latest = max(all, key=lambda x: x['CreationDate'])
                creation_time = latest['CreationDate']
                formatted_time = datetime.strptime(str(creation_time), "%Y-%m-%dT%H:%M:%S.000Z")
                ami_age = (datetime.now() - formatted_time).total_seconds()
                return self.STATUS_PRESENT, int(ami_age)

        except OSError:
            raise

    def check(self, instance):
        if 'aws_region' not in instance:
            raise Exception("Missing 'aws_region' in file check config")
        if 'ami_name' not in instance:
            raise Exception("Missing 'ami_name' in file check config")

        aws_region = instance['aws_region']
        ami_name = instance['ami_name']

        status, ami_age = self.ami_exists(aws_region, ami_name)

        tags = [
            'status:' + status,
            'ami_name:' + ami_name
        ]

        # Emit a service check:
        if status == self.STATUS_ABSENT:
            check_status = AgentCheck.CRITICAL
            msg = "AMI %s cannot be found" % (ami_name)
        else:
            check_status = AgentCheck.OK
            msg = "AMI %s found" % (ami_name)
            self.gauge('aws.ec2.ami.age_seconds', int(ami_age), tags=tags)

        self.service_check('aws.ec2.ami.existence', check_status, message=msg, tags=tags)
