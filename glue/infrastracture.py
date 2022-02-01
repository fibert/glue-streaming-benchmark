import os
from constructs import Construct
from aws_cdk import (
    aws_glue_alpha as glue_alpha,
    aws_glue as glue,
    aws_kinesis as kinesis,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_s3_assets as s3assets,
    aws_iam as iam,
    Aws,
)
import glue.cfn_columns as columns

class Glue(Construct):
    def __init__(self, scope: Construct, id_: str, data_stream: kinesis.Stream, bucket: s3.Bucket, worker_count :int = 2) -> None:
        super().__init__(scope, id_)

        self.flatten_job = None


        database = glue_alpha.Database(self, 'benchmark-database',
            database_name=f'glue-benchmark-db-{worker_count}',
        )

        # table = glue.Table(self, 'benchmark-table',
        #     table_name='glue-benchmark-json-table',
        #     database=database,
        #     data_format=glue.DataFormat.JSON,
        #     columns=columns.table_columns[:2],
        #     bucket=data_stream,
            
        # )

        # bench_stream = kinesis.Stream.from_stream_arn(self, 'aaa', stream_arn='arn:aws:kinesis:us-east-1:027179758433:stream/benchmark-1')
        # data_stream = bench_stream

        cfn_table = glue.CfnTable(
            self,
            "cfn-benchmark-table",
            catalog_id=database.catalog_id,
            database_name=database.database_name,
            table_input=glue.CfnTable.TableInputProperty(
                description="Glue Streaming Benchmark Table",
                name='cfn-benchmark-table',
                parameters={
                    "classification": "json",
                },
                table_type="EXTERNAL_TABLE",
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns.cfn_table_columns,
                    location=f"{data_stream.stream_name}",
                    parameters={
                        "endpointUrl": f"https://kinesis.{Aws.REGION}.amazonaws.com",
                        "streamName": f"{data_stream.stream_name}",
                        "typeOfData": "kinesis"
                    },
                    # input_format="org.apache.hadoop.mapred.TextInputFormat",
                    # output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    # serde_info=glue.CfnTable.SerdeInfoProperty(
                    #     name="miztiikAutomationSerDeConfig",
                    #     serialization_library="org.openx.data.jsonserde.JsonSerDe",
                    #     parameters={
                    #         "paths": "",
                    #     }
                    # )
                )
            )
        )
        cfn_table.node.add_dependency(database)


        role_glue = iam.Role(self, 'benchmark-glue-role',
            role_name=f'glue-benchmark-role-{worker_count}',
            assumed_by=iam.ServicePrincipal('glue.amazonaws.com'),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='service-role/AWSGlueServiceRole')],
        )
        role_glue.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))
        role_glue.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'))
        bucket.grant_read_write(role_glue)
        data_stream.grant_read_write(role_glue)

        # flatten_json = s3assets.Asset(self, 'benchmark-etl-script-flatten',
        #     path='glue/etl_scripts/flatten_json.py',
        #     readers=[role_glue],
        # )

        asset_protobuf_jar = s3assets.Asset(self, 'protobuf-jar',
            path='glue/jars/protobuf-java-3.11.4.jar',
            # readers=[role_glue],
        )
        # asset_protobuf_jar.grant_read(role_glue)

        deployment_protobuf_jar = s3deploy.BucketDeployment(self, 'populate-jars',
            sources=[s3deploy.Source.asset('glue/jars')],
            destination_bucket=bucket,
            destination_key_prefix='jars/'
        )

        table_name = cfn_table.table_input.name
        etl_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'etl_scripts/flatten_json_new.py')
        id_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'etl_scripts/id_streaming.py')


        self.flatten_job = glue_alpha.Job(self, 'benchmark-streaming-job',
            job_name=f'flatten_json_{worker_count}',
            executable=glue_alpha.JobExecutable.python_streaming(
                glue_version=glue_alpha.GlueVersion.V3_0,
                python_version=glue_alpha.PythonVersion.THREE,
                script=glue_alpha.Code.from_asset(etl_path)
            ),
            enable_profiling_metrics=True,
            max_concurrent_runs=1,
            role=role_glue,
            default_arguments={
                '--EVENT_TYPES': 'testevent',
                '--STAGING_PATH': f"{bucket.s3_url_for_object('flatten/staging/')}",
                '--WINDOW_SIZE': '10 seconds',
                '--OUTPUT_PATH': f"{bucket.s3_url_for_object('flatten/output/')}",
                '--INPUT_DB': f"{database.database_name}",
                '--CHECKPOINT_LOCATION': f"{bucket.s3_url_for_object('flatten/checkpoint/')}",
                '--INPUT_TABLE': f"{table_name}",
                "--extra-jars": f"{bucket.s3_url_for_object('jars/protobuf-java-3.11.4.jar')}",
                "--user-jars-first": "true",
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': f's3://fibertdf-spark-ui-logs/flatten-{worker_count}',
            },
            worker_count=worker_count,
            worker_type=glue_alpha.WorkerType.G_1_X,
            max_retries=0,
        )



        bucket_spark_ui_logs = s3.Bucket.from_bucket_name(self, 'Spark-ui-logs', 'fibertdf-spark-ui-logs')
        bucket_spark_ui_logs.grant_read_write(role_glue)

