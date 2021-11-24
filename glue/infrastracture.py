import os
from aws_cdk import (
    core as cdk,
    aws_glue as glue,
    aws_kinesis as kinesis,
    aws_s3 as s3,
    aws_s3_assets as s3assets,
    aws_iam as iam,
)
import glue.cfn_columns as columns

class Glue(cdk.Construct):
    def __init__(self, scope: cdk.Construct, id_: str, data_stream: kinesis.Stream, bucket: s3.Bucket) -> None:
        super().__init__(scope, id_)

        database = glue.Database(self, 'benchmark-database',
            database_name='glue-benchmark-db',
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
                # parameters={
                #     "classification": "json",
                # },
                table_type="EXTERNAL_TABLE",
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=columns.cfn_table_columns,
                    location=f"{data_stream.stream_name}",
                    parameters={
                        "endpointUrl": f"https://kinesis.{cdk.Aws.REGION}.amazonaws.com",
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
            role_name='glue-benchmark-role',
            assumed_by=iam.ServicePrincipal('glue.amazonaws.com'),
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='service-role/AWSGlueServiceRole')],
        )
        bucket.grant_read_write(role_glue)
        data_stream.grant_read_write(role_glue)

        # flatten_json = s3assets.Asset(self, 'benchmark-etl-script-flatten',
        #     path='glue/etl_scripts/flatten_json.py',
        #     readers=[role_glue],
        # )

        table_name = cfn_table.table_input.name
        etl_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'etl_scripts/flatten_json.py')


        job = glue.Job(self, 'benchmark-streaming-job',
            job_name='flatten_json',
            executable=glue.JobExecutable.python_streaming(
                glue_version=glue.GlueVersion.V2_0,
                python_version=glue.PythonVersion.THREE,
                script=glue.Code.from_asset(etl_path)
            ),
            enable_profiling_metrics=True,
            max_concurrent_runs=1,
            role=role_glue,
            default_arguments={
                '--EVENT_TYPES': 'testevent',
                '--STAGING_PATH': f"{bucket.s3_url_for_object('staging/')}",
                '--WINDOW_SIZE': '60 seconds',
                '--OUTPUT_PATH': f"{bucket.s3_url_for_object('output/')}",
                '--INPUT_DB': f"{database.database_name}",
                '--CHECKPOINT_LOCATION': f"{bucket.s3_url_for_object('checkpoint/')}",
                '--INPUT_TABLE': f"{table_name}",
            },
            worker_count=2,
            worker_type=glue.WorkerType.G_1_X,
            max_retries=0,
        )


# job_cases_and_death_raw_to_transformed = glue.CfnJob(self, 'Job_Cases_And_death_Raw_To_Transformed',
#             name='covid-19-cases-and-death-raw-to-transformed-job',
#             command=glue.CfnJob.JobCommandProperty(
#                 name='glueetl',
#                 python_version='3',
#                 script_location=asset_etl_script_cases_and_death.s3_object_url,
#             ),
#             default_arguments={
#                 '--enable-glue-datacatalog': '""',
#                 '--source_database_name': database_covid_raw.database_name,
#                 '--source_table_name': 'cases_and_death',
#                 '--target_database_name': database_covid_transformed.database_name,
#                 '--target_bucket': bucket_transformed.bucket_name,
#                 '--target_table_name': 'cases_and_death',
#                 '--TempDir': f's3://{bucket_glue.bucket_name}/etl/raw-to-transformed',
#                 "--job-bookmark-option": "job-bookmark-enable",
#             },
#             execution_property=glue.CfnJob.ExecutionPropertyProperty(
#                 max_concurrent_runs=1,
#             ),
#             glue_version='2.0',
#             max_retries=0,
#             number_of_workers=2,
#             role=role_glue.role_arn,
#             worker_type='G.1X',
#         )
#         job_cases_and_death_raw_to_transformed.node.add_dependency(asset_etl_script_cases_and_death)
#         job_cases_and_death_raw_to_transformed.node.add_dependency(database_covid_raw)
#         job_cases_and_death_raw_to_transformed.node.add_dependency(database_covid_transformed)
#         job_cases_and_death_raw_to_transformed.node.add_dependency(bucket_transformed)
#         job_cases_and_death_raw_to_transformed.node.add_dependency(bucket_glue)



        