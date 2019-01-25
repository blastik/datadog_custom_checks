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


class S3FileCheck(AgentCheck):

    STATUS_ABSENT = 'absent'
    STATUS_PRESENT = 'present'

    def s3_file_exist(self, bucket, search_key):
        try:
            client = boto3.client('s3')
            response = client.list_objects_v2(
                Bucket=bucket,
                Delimiter='/',
                Prefix=search_key,
            )
            if 'Contents' in response:
                all = response['Contents']
                latest = max(all, key=lambda x: x['LastModified'])
                modified_time = latest['LastModified']
                formatted_time = datetime.strptime(str(modified_time), "%Y-%m-%d %H:%M:%S+00:00")
                file_age = (datetime.now() - formatted_time).total_seconds()
                return self.STATUS_PRESENT, file_age
            else:
                return self.STATUS_ABSENT, []

        except OSError:
            raise

    def check(self, instance):
        if 'bucket' not in instance:
            raise Exception("Missing 'bucket' in file check config")
        if 'search_key' not in instance:
            raise Exception("Missing 'search_key' in file check config")

        bucket = instance['bucket']
        search_key = instance['search_key']

        status, file_age = self.s3_file_exist(bucket, search_key)

        tags = [
            'status:' + status,
            'bucket:' + bucket,
            'search_key:' + search_key
        ]

        # Emit a service check:
        if status == self.STATUS_ABSENT:
            check_status = AgentCheck.CRITICAL
            msg = "File %s cannot be found into %s" % (search_key, bucket)
        else:
            check_status = AgentCheck.OK
            msg = "File %s found into %s" % (search_key, bucket)
            self.gauge('aws.s3.file.age_seconds', int(file_age), tags=tags)

        self.service_check('aws.s3.file.existence', check_status, message=msg, tags=tags)
