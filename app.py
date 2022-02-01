#!/usr/bin/env python3
import os
from aws_cdk import App
from deployment import BenchmarkConsumer

app = App()

glue_worker_count = 20

datastream_name = f'benchmark-data-stream-{glue_worker_count}'
datastream_shards = (glue_worker_count-1) * 4
BenchmarkConsumer(app, f"GlueBenchmarkStack-{glue_worker_count}", 
    datastream_name=datastream_name,
    datastream_shards=datastream_shards,
    glue_worker_count=glue_worker_count,
)

app.synth()
