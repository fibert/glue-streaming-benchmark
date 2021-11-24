from aws_cdk import core as cdk
from glue.infrastracture import Glue
from kinesis.infrastracture import Kinesis
from s3.infrastracture import S3


class BenchmarkConsumer(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id_: str, **kwargs) -> None:
        super().__init__(scope, id_, **kwargs)

        kinesis = Kinesis(self, 'Kinesis')
        s3 = S3(self, 'S3')
        glue = Glue(self, "Glue", 
                    data_stream=kinesis.data_stream, 
                    bucket=s3.bucket)
        
        cdk.CfnOutput(
            self,
            "Kinesis-Data-Stream",
            value=kinesis.data_stream.stream_name,
        )