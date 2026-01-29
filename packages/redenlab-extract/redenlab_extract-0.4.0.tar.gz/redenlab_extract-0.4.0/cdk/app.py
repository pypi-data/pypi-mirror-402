#!/usr/bin/env python3
import os

import aws_cdk as cdk
from cdk.pipeline_stack import PipelineStack

app = cdk.App()

# Deploy CI/CD pipeline for redenlab-extract package
PipelineStack(
    app,
    "RedenlabExtractPipeline",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region='us-west-2'  # Match CodeCommit region
    ),
    description="CI/CD pipeline for redenlab-extract Python package - PR validation and PyPI publishing"
)

app.synth()
