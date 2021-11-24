from aws_cdk import (
    core as cdk,
    aws_kinesis as kinesis,
)

class Kinesis(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id_: str) -> None:
        super().__init__(scope, id_)

        self.data_stream = kinesis.Stream(self, 'benchmark-stream',
            stream_name='benchmark-2',
            shard_count=1,
            retention_period=cdk.Duration.hours(24),
        )