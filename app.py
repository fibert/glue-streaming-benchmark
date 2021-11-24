#!/usr/bin/env python3
import os
from aws_cdk import core as cdk
from deployment import BenchmarkConsumer


app = cdk.App()
BenchmarkConsumer(app, "GlueBenchmarkStack")

app.synth()
