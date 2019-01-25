# My Datadog custom checks

# Directory Layout

```
checks.d/           # custom checks python scripts
conf.d/             # custom check config examples
```

## s3_file

Checks if a file exists in a particular AWS S3 bucket. If it does, the metric `aws.s3.file.age_seconds` shows the file age in seconds.
If the S3 file is not found, the custom check monitor triggers a `Critical` alert, otherwise `OK`.
This check should be executed from instances with the apropiate IAM role permissions.

## ec2_ami

Checks if a EC2 AMI exists. If it does, the metric `aws.ec2.ami.age_seconds` shows the file age in seconds.
If the AMI is not found, the custom check monitor triggers a `Critical` alert, otherwise `OK`.
This check should be executed from instances with the apropiate IAM role permissions.
