from constructs import Construct
from aws_cdk import (
    aws_kinesis as kinesis,
    Duration,
)

class Kinesis(Construct):
    def __init__(self, scope: Construct, id_: str, stream_name: str, shard_count :int = 1) -> None:
        super().__init__(scope, id_)

        
        
        self.data_stream = kinesis.Stream(self, 'benchmark-stream',
            stream_name=stream_name,
            shard_count=shard_count,
            retention_period=Duration.hours(24),
        )