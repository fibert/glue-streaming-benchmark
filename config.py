from math import ceil

# Glue
GLUE_JOB_WORKERS = 30
GLUE_JOB_NAME = f'flatten-json-{GLUE_JOB_WORKERS}'
GLUE_JOB_ROLE_NAME = f'glue-benchmark-role-{GLUE_JOB_WORKERS}'

GLUE_JOB_ETL_SCRIPT = 'etl_scripts/flatten_json_new.py'
GLUE_JOB_PARAMETER_WINDOW_SIZE = '10 seconds'
GLUE_JOB_PARAMETER_STAGING_PATH = 'flatten/staging/'
GLUE_JOB_PARAMETER_OUTPUT_PATH = 'flatten/output/'
GLUE_JOB_PARAMETER_CHECKPOINT_PATH = 'flatten/checkpoint/'


GLUE_DATABASE_NAME = f"glue-benchmark-db-{GLUE_JOB_WORKERS}"
GLUE_TABLE_NAME = "glue-benchmark-table"

GLUE_JOB_SPARK_EVENT_LOGS_PATH = f's3://fibertdf-spark-ui-logs/flatten-{GLUE_JOB_WORKERS}'
GLUE_JOB_SPARK_UI_LOGS_S3_BUCKET = GLUE_JOB_SPARK_EVENT_LOGS_PATH.split('/')[2] # needed for granting the glue job write permission



# Kinesis
KINESIS_DATASTREAM_NAME = f'benchmark-data-stream-{GLUE_JOB_WORKERS}'
KINESIS_DATASTREAM_SHARDS = (GLUE_JOB_WORKERS-1) * 4



# S3 streaming job output bucket
S3_OUTPUT_BUCKET_NAME = f'glue-benchmark-output-bucket-{GLUE_JOB_WORKERS}'



# AutoScaling group producer
AUTOSCALING_GROUP_CAPACITY = ceil(GLUE_JOB_WORKERS / 10)
AUTOSCALING_GROUP_INSTANCE_TYPE = 'c5.xlarge'
AUTOSCALING_EC2_KEY_PAIR_NAME = "fibertdf"

EC2_PRODUCER_RPS_MIN = ceil(((GLUE_JOB_WORKERS * 1000) - 5000) / AUTOSCALING_GROUP_CAPACITY)
EC2_PRODUCER_RPS_STEP = ceil(1000 / AUTOSCALING_GROUP_CAPACITY)
EC2_PRODUCER_RPS_MAX = ceil(((GLUE_JOB_WORKERS * 1000) + 6000) / AUTOSCALING_GROUP_CAPACITY)
