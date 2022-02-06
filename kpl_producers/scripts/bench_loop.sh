#!/bin/bash

mvn clean package

glue_job_name=$GLUE_JOB_NAME
aws glue start-job-run --job-name $glue_job_name


sleep 30


outfile="output-loop"
echo "Benchmark started at $(date):"> $outfile
echo >> $outfile


stream_name=$KINESIS_DATASTREAM
region=$AWS_DEFAULT_REGION
producer_running_time=$PRODUCER_RUNNING_TIME

sleep_time_between_runs=$(expr 60 \* 10)

echo PRODUCER_RPS_MIN=$PRODUCER_RPS_MIN >> $outfile
echo PRODUCER_RPS_MAX=$PRODUCER_RPS_MAX >> $outfile
echo PRODUCER_RPS_STEP=$PRODUCER_RPS_STEP >> $outfile
echo >> $outfile

for (( records_per_sec=$PRODUCER_RPS_MIN ;  records_per_sec<=$PRODUCER_RPS_MAX ; records_per_sec+=$PRODUCER_RPS_STEP ))
do 

    args="$stream_name $region $producer_running_time $records_per_sec"

    start_time=$(date)
    mvn exec:java -e -Dexec.mainClass="com.amazonaws.services.kinesis.producer.sample.SampleProducer" -Dexec.args="$args" && status="SUCCESS" || status="FAIL"
    end_time=$(date)

    echo 
    echo "Status: $status" 
    echo "Args: $args"
    echo "Start Time: $start_time" 
    echo "End Time: $end_time" 
    echo 

    echo >> $outfile
    echo "Status: $status" >> $outfile
    echo "Args: $args" >> $outfile
    echo "Start Time: $start_time" >> $outfile
    echo "End Time: $end_time" >> $outfile
    echo >> $outfile

    sleep $sleep_time_between_runs
done