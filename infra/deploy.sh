#!/bin/bash

# Exit if any command fails
set -e

# Deploy CDK stack and capture outputs
cdk deploy --outputs-file ../cdk-outputs.json
