import os
from constructs import Construct
from aws_cdk import (
    aws_glue_alpha as glue_alpha,
    aws_glue as glue,
    aws_kinesis as kinesis,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    Aws,
)
from . cfn_columns import  cfn_table_columns as columns 

import config

class Glue(Construct):
    def __init__(self, scope: Construct, id_: str, data_stream: kinesis.Stream, bucket: s3.Bucket) -> None:
        super().__init__(scope, id_)

        self.flatten_job = None


        database = glue_alpha.Database(self, 'benchmark-database',
            database_name=config.GLUE_DATABASE_NAME,
        )


        cfn_table = glue.CfnTable(
            self,
            "glue-benchmark-table",
            catalog_id=database.catalog_id,
            database_name=database.database_name,
            table_input=glue.CfnTable.TableInputProperty(
                description="Glue Streaming Benchmark Table",
                name=config.GLUE_TABLE_NAME,
                parameters={
                    "classification": "json",
                },
                table_type="EXTERNAL_TABLE",
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns,
                    location=f"{data_stream.stream_name}",
                    parameters={
                        "endpointUrl": f"https://kinesis.{Aws.REGION}.amazonaws.com",
                        "streamName": f"{data_stream.stream_name}",
                        "typeOfData": "kinesis"
                    },
                )
            )
        )
        cfn_table.node.add_dependency(database)


        role_glue = iam.Role(self, 'benchmark-glue-role',
            role_name=config.GLUE_JOB_ROLE_NAME,
            assumed_by=iam.ServicePrincipal('glue.amazonaws.com'),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='service-role/AWSGlueServiceRole')],
        )
        role_glue.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))
        role_glue.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchLogsFullAccess'))
        bucket.grant_read_write(role_glue)
        data_stream.grant_read_write(role_glue)

        deployment_protobuf_jar = s3deploy.BucketDeployment(self, 'populate-jars',
            sources=[s3deploy.Source.asset(f'{os.path.dirname(os.path.abspath(__file__))}/jars')],
            destination_bucket=bucket,
            destination_key_prefix='jars/'
        )

        etl_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), config.GLUE_JOB_ETL_SCRIPT)


        self.flatten_job = glue_alpha.Job(self, 'glue-benchmark-streaming-job',
            job_name=config.GLUE_JOB_NAME,
            executable=glue_alpha.JobExecutable.python_streaming(
                glue_version=glue_alpha.GlueVersion.V3_0,
                python_version=glue_alpha.PythonVersion.THREE,
                script=glue_alpha.Code.from_asset(etl_path)
            ),
            enable_profiling_metrics=True,
            max_concurrent_runs=1,
            role=role_glue,
            default_arguments={
                '--INPUT_DB': f"{database.database_name}",
                '--INPUT_TABLE': f"{cfn_table.table_input.name}",
                '--EVENT_TYPES': 'testevent',
                '--WINDOW_SIZE': config.GLUE_JOB_PARAMETER_WINDOW_SIZE,
                '--STAGING_PATH': f"{bucket.s3_url_for_object(config.GLUE_JOB_PARAMETER_STAGING_PATH)}",
                '--OUTPUT_PATH': f"{bucket.s3_url_for_object(config.GLUE_JOB_PARAMETER_OUTPUT_PATH)}",
                '--CHECKPOINT_LOCATION': f"{bucket.s3_url_for_object(config.GLUE_JOB_PARAMETER_CHECKPOINT_PATH)}",
                "--extra-jars": f"{bucket.s3_url_for_object('jars/protobuf-java-3.11.4.jar')}",
                "--user-jars-first": "true",
                '--enable-spark-ui': 'true',
                '--spark-event-logs-path': config.GLUE_JOB_SPARK_EVENT_LOGS_PATH,
            },
            worker_count=config.GLUE_JOB_WORKERS,
            worker_type=glue_alpha.WorkerType.G_1_X,
            max_retries=0,
        )


        spark_ui_bucket = config.GLUE_JOB_SPARK_EVENT_LOGS_PATH.split('/')[2]
        bucket_spark_ui_logs = s3.Bucket.from_bucket_name(self, 'Spark-ui-logs', spark_ui_bucket)
        bucket_spark_ui_logs.grant_read_write(role_glue)

