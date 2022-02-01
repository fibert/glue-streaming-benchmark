from constructs import Construct
from aws_cdk import (
    Stack,
    CfnParameter,
    CfnOutput,
)

from math import ceil

from glue.infrastracture import Glue
from kinesis.infrastracture import Kinesis
from s3.infrastracture import S3
from ec2autoscaling.infrastracture import AutoScaling


class BenchmarkConsumer(Stack):
    def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        kinesis = Kinesis(self, 'Kinesis')

        s3 = S3(self, 'S3')
        
        glue = Glue(self, "Glue", 
            data_stream=kinesis.data_stream,
            bucket=s3.bucket,
        )

        autoscale = AutoScaling(self, "AutoScaling",
            kinesis_data_stream=kinesis.data_stream,
            glue_job=glue.flatten_job,
            bucket=s3.bucket,
        )