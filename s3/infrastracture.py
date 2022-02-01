from constructs import Construct
from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy
)

class S3(Construct):
    def __init__(self, scope: Construct, id_: str, glue_worker_count: int) -> None:
        super().__init__(scope, id_)

        self.bucket = s3.Bucket(self, 'benchmark-output-bucket',
            bucket_name=f'glue-benchmark-output-bucket-{glue_worker_count}',
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY
        )