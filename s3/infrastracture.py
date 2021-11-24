from aws_cdk import (
    core as cdk,
    aws_s3 as s3,
)

class S3(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id_: str) -> None:
        super().__init__(scope, id_)

        self.bucket = s3.Bucket(self, 'benchmark-output-bucket',
            bucket_name='glue-benchmark-output-bucket',
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )