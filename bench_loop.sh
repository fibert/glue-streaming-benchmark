#!/bin/bash

mvn clean package

glue_job_name=$GLUE_JOB_NAME
aws glue start-job-run --job-name $glue_job_name


sleep 30


outfile="output-loop"
echo > $outfile

stream_name=$KINESIS_DATASTREAM
region=$AWS_DEFAULT_REGION
producer_running_time=1800

sleep_time_between_runs=$(expr 60 \* 10)

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

