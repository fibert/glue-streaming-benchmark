
# Glue Streaming Benchmark

![CDK diagram](/docs/diagram.png)

## Prerequisites
1. Install CDK
2. Install python dependencies in a virutal env
3. Create a CloudWatch dashboard
4. Create an S3 bucket for Spark-UI logs

### Install CDK
Install the AWS CDK Toolkit globally using the following Node Package Manager command.
```
npm install -g aws-cdk
```

```
cdk --version
```

### How to work with CDK

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

### How to create a CloudWatch dashboard

- Open [dashboard.template.json](dashboard.template.json)
- Replace every occurence of `{{JOB_NAME}}` with your Glue streaming job name
- Replace every occurence of `{{DATASTREAM_NAME}}` with your Kinesis DataStream name
- In CloudWatch, create a new empty dashboard
- Click on **Actions** -> **View/edit source**
- Paste the JSON edited file 


## Usage

You can edit the configuration at (config.py)[config.py], noticable parameters:
- `GLUE_JOB_WORKERS` - Number of workers for the glue job
- `GLUE_JOB_ETL_SCRIPT` - The ETL script path for the job
- `GLUE_JOB_SPARK_EVENT_LOGS_PATH` - The S3 bucket for the Spark-UI logs
- `S3_OUTPUT_BUCKET_NAME` - The S3 bucket for the glue job output
- `AUTOSCALING_EC2_KEY_PAIR_NAME` - The keypair to use in the EC2 instances

### Deploy
To create the app run the following command:
```
cdk deploy --require-approval never
```

After the deployment is finished all the resources will be created.


### Destroy
To destroy the stack run the following command
```
cdk destroy -f
```