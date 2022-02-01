from math import ceil

# ----- Glue ----- 
GLUE_JOB_WORKERS = 10
GLUE_JOB_NAME = f'flatten-json-{GLUE_JOB_WORKERS}'
GLUE_JOB_ROLE_NAME = f'glue-benchmark-role-{GLUE_JOB_WORKERS}'

GLUE_JOB_ETL_SCRIPT = 'etl_scripts/flatten_json_new.py'
GLUE_JOB_PARAMETER_WINDOW_SIZE = '10 seconds'
GLUE_JOB_PARAMETER_STAGING_PATH = 'flatten/staging/'
GLUE_JOB_PARAMETER_OUTPUT_PATH = 'flatten/output/'
GLUE_JOB_PARAMETER_CHECKPOINT_PATH = 'flatten/checkpoint/'


GLUE_DATABASE_NAME = f"glue-benchmark-db-{GLUE_JOB_WORKERS}"
GLUE_TABLE_NAME = "glue-benchmark-table"

# This CDK app does not create this bucket for you
GLUE_JOB_SPARK_EVENT_LOGS_PATH = f's3://fibertdf-spark-ui-logs/flatten-{GLUE_JOB_WORKERS}'




# ----- Kinesis -----
KINESIS_DATASTREAM_NAME = f'benchmark-data-stream-{GLUE_JOB_WORKERS}'
KINESIS_DATASTREAM_SHARDS = (GLUE_JOB_WORKERS-1) * 4



# ----- S3 streaming job output bucket ----- 
# This bucket is created for you in this stack
S3_OUTPUT_BUCKET_NAME = f'glue-benchmark-output-bucket-{GLUE_JOB_WORKERS}'



# ----- AutoScaling group producer ----- 
AUTOSCALING_EC2_KEY_PAIR_NAME = "fibertdf"
AUTOSCALING_GROUP_INSTANCE_TYPE = 'c5.xlarge' # default: c5.xlarge

# Number of EC2 instances to create, recommended that each EC2 instance will send up to 10,000 messages/sec
# default: ceil(#Workers / 10)
AUTOSCALING_GROUP_CAPACITY = ceil(GLUE_JOB_WORKERS / 10)

# The starting messages/sec, stopping messages/sec and the step
EC2_PRODUCER_RPS_MIN = ceil(((GLUE_JOB_WORKERS * 1000) - 5000) / AUTOSCALING_GROUP_CAPACITY)
EC2_PRODUCER_RPS_STEP = ceil(1000 / AUTOSCALING_GROUP_CAPACITY)
EC2_PRODUCER_RPS_MAX = ceil(((GLUE_JOB_WORKERS * 1000) + 6000) / AUTOSCALING_GROUP_CAPACITY)

# Time in seconds for the producer to work each iteration, default: 1800 (30 minutes)
EC2_PRODUCER_RUNNING_TIME = 1800
