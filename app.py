#!/usr/bin/env python3
import os
from aws_cdk import App
from deployment import BenchmarkConsumer

import config

app = App()


BenchmarkConsumer(app, f"GlueBenchmarkStack-{config.GLUE_JOB_WORKERS}")

app.synth()
