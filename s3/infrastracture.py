from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy
)

import config

class S3(Construct):
    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)

        self.bucket = s3.Bucket(self, 'glue-benchmark-output-bucket',
            bucket_name=config.S3_OUTPUT_BUCKET_NAME,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )