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
from ec2autoscaling.infrastracture import AUTOSCALING


class BenchmarkConsumer(Stack):
    def __init__(self, scope: Construct, id_: str, datastream_name: str, datastream_shards: int, glue_worker_count: int, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        kinesis = Kinesis(self, 'Kinesis', 
            stream_name=datastream_name,
            shard_count=datastream_shards,
        )

        s3 = S3(self, 'S3',
            glue_worker_count=glue_worker_count,
        )
        
        glue = Glue(self, "Glue", 
            data_stream=kinesis.data_stream,
            bucket=s3.bucket,
            worker_count=glue_worker_count,
        )

        autoscale = AUTOSCALING(self, "AutoScaling",
            instance_type="c5.xlarge",
            capacity=5, #ceil(glue_worker_count / 10),
            key_name='fibertdf',
            kinesis_data_stream=kinesis.data_stream,
            glue_job=glue.flatten_job,
            glue_worker_count=glue_worker_count,
            bucket=s3.bucket,
        )