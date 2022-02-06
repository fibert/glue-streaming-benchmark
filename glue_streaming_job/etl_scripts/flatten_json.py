import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from awsglue.dynamicframe import DynamicFrame
from awsglue import DynamicFrame
 
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
 
# ----- get job params
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'WINDOW_SIZE', 'CHECKPOINT_LOCATION', 'STAGING_PATH', 'OUTPUT_PATH',
                                     'INPUT_DB', 'INPUT_TABLE', 'EVENT_TYPES'])
windowSize = args['WINDOW_SIZE']
checkpointLocation = args['CHECKPOINT_LOCATION']
stagingPath = args['STAGING_PATH']
outputPath = args['OUTPUT_PATH']
inputGlueCatalogDB = args['INPUT_DB']
inputGlueCatalogTable = args['INPUT_TABLE']
eventTypes = args['EVENT_TYPES']
 
 
def is_schema_null(dynamic_frame):
    for field in dynamic_frame.schema():
        return False
    return True
 
 
def process_micro_batch(data_frame, batch_id):
    data_frame.cache()
   
    print("DATA FRAME SCHEMA########################################################\n")
    data_frame.printSchema()
    print("DATA FRAME DATA########################################################\n")
    data_frame.show(3)
    json_schema = spark.read.json(data_frame.rdd.map(lambda row: row[0])).schema
    print("INFERED SCHEMA========>\n")
    print(json_schema)
 
    # convert Spark DataFrame to Glue Dynamic DataFrame
    data_source_ddf = DynamicFrame.fromDF(dataframe=data_frame, glue_ctx=glueContext, name="data_source")
 
    # iterate over events and write them to S3
    for event in eventTypes.split(','):
        print(f"event: {event}")
        specific_events_ddf = Filter.apply(frame=data_source_ddf, f=lambda x: x['eventtype'] == event)
 
        # check if resulting dynamic data frame is empty
        if is_schema_null(specific_events_ddf):
            print("specific_events_ddf is empty!")
            continue
 
 
         # flatten the data
        dfc = Relationalize.apply(frame=specific_events_ddf,
                              staging_path=stagingPath,
                              name='flatten_table',
                              transformation_ctx="dfc")
 
        flattened_frame_ddf = dfc.select('flatten_table')
 
        # output partitioned data to S3
        conn_options_sink = {"path": outputPath,
                             "partitionKeys": []}
 
        glueContext.write_dynamic_frame.from_options(frame=flattened_frame_ddf,
                                                     connection_type="s3",
                                                     connection_options=conn_options_sink,
                                                     format="csv",
                                                     transformation_ctx="data_sink")
    data_frame.unpersist()
 
 
# read from kinesis stream into create a spark DF
data_frame_datasource = glueContext.create_data_frame.from_catalog(database=inputGlueCatalogDB,
                                                                   table_name=inputGlueCatalogTable,
                                                                   additional_options={"startingPosition": "latest",
                                                                                       "inferSchema": "false",
                                                                                       "maxFetchTimeInMs": 20000,
                                                                                       "addIdleTimeBetweenReads": "true",
                                                                                       "idleTimeBetweenReadsInMs": 1000})
 
# process every micro batch
glueContext.forEachBatch(frame=data_frame_datasource, batch_function=process_micro_batch,
                         options={"windowSize": windowSize, "checkpointLocation": checkpointLocation})
job.commit()