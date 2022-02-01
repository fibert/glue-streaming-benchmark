import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

from pyspark.sql import DataFrame, Row
import datetime
from awsglue import DynamicFrame

args = getResolvedOptions(sys.argv, ["JOB_NAME", "REGION", "DATABASE_NAME", "TABLE_NAME", "STARTING_POSITION", "OUTPUT_PATH", "CHECKPOINT_LOCATION", "INFER_SCHEMA"])

region = args["REGION"]
kinesis_stream_starting_position = args["STARTING_POSITION"]

glue_database = args["DATABASE_NAME"]
glue_table = args["TABLE_NAME"]

s3_output_path = args["OUTPUT_PATH"]
s3_checkpoint_location = args["CHECKPOINT_LOCATION"]

do_infer_schema = args["INFER_SCHEMA"]

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node Kinesis Stream
dataframe_KinesisStream_node1 = glueContext.create_data_frame.from_catalog(
    database=glue_database,
    table_name=glue_table,
    additional_options={"startingPosition": kinesis_stream_starting_position, "inferSchema": do_infer_schema},
)


def processBatch(data_frame, batchId):
    if data_frame.count() > 0:
        KinesisStream_node1 = DynamicFrame.fromDF(
            data_frame, glueContext, "from_data_frame"
        )
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour

        # Script generated for node S3 bucket
        S3bucket_node3_path = (
            s3_output_path
            + "/"
        )
        
        S3bucket_node3 = glueContext.write_dynamic_frame.from_options(
            frame=KinesisStream_node1,
            connection_type="s3",
            format="json",
            connection_options={"path": S3bucket_node3_path, "partitionKeys": []},
        )


glueContext.forEachBatch(
    frame=dataframe_KinesisStream_node1,
    batch_function=processBatch,
    options={
        "windowSize": "10 seconds",
        "checkpointLocation": s3_checkpoint_location,
    },
)
job.commit()