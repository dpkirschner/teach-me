# Infrastructure Deployment

This directory contains AWS CDK infrastructure code for the Teach Me project.

This assumes that you have the teach_me dev user creds from AWS. Swap this with any other profile you have.

## Prerequisites

- AWS CDK CLI installed globally: `npm install -g aws-cdk`
- AWS credentials configured with the `teach_me` profile
- Python 3.x installed

## Deployment Instructions

1. **Install dependencies** (if requirements.txt exists):
   ```bash
   pip install -r requirements.txt
   ```

2. **Bootstrap CDK** (one-time setup per AWS account/region):
   ```bash
   cdk bootstrap --profile teach_me
   ```

3. **Deploy the stack**:
   ```bash
   cdk deploy --profile teach_me
   ```

## Other Useful Commands

- **Synthesize CloudFormation template**: `cdk synth --profile teach_me`
- **View differences**: `cdk diff --profile teach_me`
- **Destroy stack**: `cdk destroy --profile teach_me`