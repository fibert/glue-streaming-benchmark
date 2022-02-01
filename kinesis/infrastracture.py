from constructs import Construct
from aws_cdk import (
    aws_kinesis as kinesis,
    Duration,
)

import config

class Kinesis(Construct):
    def __init__(self, scope: Construct, id_: str) -> None:
        super().__init__(scope, id_)

        
        self.data_stream = kinesis.Stream(self, 'glue-benchmark-datastream',
            stream_name=config.KINESIS_DATASTREAM_NAME,
            shard_count=config.KINESIS_DATASTREAM_SHARDS,
            retention_period=Duration.hours(24),
        )