from constructs import Construct
from aws_cdk import (
    Stack,
    CfnOutput,
)

from glue_streaming_job.infrastracture import Glue
from kinesis_datastream.infrastracture import Kinesis
from s3_output_bucket.infrastracture import S3
from kpl_producers.infrastracture import AutoScaling

import config

class BenchmarkConsumer(Stack):
    def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        kinesis = Kinesis(self, 'Kinesis-DataStream')

        s3 = S3(self, 'S3-Output-Bucket')
        
        glue = Glue(self, "Glue-Streaming-Job", 
            data_stream=kinesis.data_stream,
            bucket=s3.bucket,
        )

        autoscale = AutoScaling(self, "KPL-Producers",
            kinesis_data_stream=kinesis.data_stream,
            glue_job=glue.flatten_job,
            bucket=s3.bucket,
        )



        

        CfnOutput(self, 'Glue Streaming Job Name',
            value=config.GLUE_JOB_NAME,
        )

        CfnOutput(self, 'Kinesis DataStream Name',
            value=config.KINESIS_DATASTREAM_NAME,
        )