# CI/CD Pipeline Setup Guide

This guide walks you through deploying the CI/CD pipeline for the redenlab-extract Python package using AWS CDK.

## Prerequisites

### 1. AWS Credentials

Ensure you have AWS credentials configured with permissions for:
- CodePipeline
- CodeBuild
- CodeCommit
- S3
- IAM
- EventBridge
- Secrets Manager
- CloudFormation

Configure credentials:
```bash
aws configure
```

Verify access:
```bash
aws sts get-caller-identity
```

### 2. PyPI API Token

You need a PyPI API token to publish packages.

**Generate PyPI Token:**
1. Log in to [pypi.org](https://pypi.org)
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Name: `redenlab-extract-cicd`
5. Scope: Select "Entire account" or limit to `redenlab-extract` project
6. Copy the token (starts with `pypi-AgE...`)

**Store in AWS Secrets Manager:**
```bash
aws secretsmanager create-secret \
  --name redenlab-extract/pypi \
  --description "PyPI credentials for redenlab-extract package publishing" \
  --secret-string '{"username":"__token__","password":"pypi-AgEXXXXXXXXX"}' \
  --region us-west-2
```

Replace `pypi-AgEXXXXXXXXX` with your actual token.

Verify the secret was created:
```bash
aws secretsmanager describe-secret \
  --secret-id redenlab-extract/pypi \
  --region us-west-2
```

### 3. CDK CLI

Install the AWS CDK CLI globally:
```bash
npm install -g aws-cdk
```

Verify installation:
```bash
cdk --version
```

### 4. Python Dependencies

The CDK project already exists in the `cdk/` directory. Install dependencies:
```bash
cd cdk/
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Step-by-Step Deployment

### Step 1: Verify CDK Bootstrap

Check if your AWS account/region is already bootstrapped:
```bash
aws cloudformation describe-stacks \
  --stack-name CDKToolkit \
  --region us-west-2
```

If you get an error (stack doesn't exist), bootstrap now:
```bash
cdk bootstrap aws://ACCOUNT-ID/us-west-2
```

Replace `ACCOUNT-ID` with your AWS account ID from `aws sts get-caller-identity`.

### Step 2: Review the CDK Stack

From the `cdk/` directory, synthesize the CloudFormation template to review:
```bash
cd cdk/
cdk synth
```

This generates CloudFormation templates in `cdk.out/`. Review the output to understand what resources will be created.

### Step 3: Deploy the Pipeline

Deploy the CDK stack:
```bash
cdk deploy
```

You'll see a summary of changes. Type `y` to confirm and deploy.

**Expected resources created:**
- S3 bucket: `redenlab-extract-pipeline-artifacts`
- CodeBuild projects: `redenlab-extract-pr-validation`, `redenlab-extract-release`
- CodePipeline pipelines: `redenlab-extract-pr-validation`, `redenlab-extract-release`
- EventBridge rules for triggering pipelines
- IAM roles and policies

Deployment takes ~3-5 minutes.

### Step 4: Verify Deployment

Check that the pipelines were created:
```bash
aws codepipeline list-pipelines --region us-west-2
```

You should see:
- `redenlab-extract-pr-validation`
- `redenlab-extract-release`

### Step 5: Commit Pipeline Configuration

The buildspec files need to be in the repository for CodeBuild to use them:
```bash
cd ..  # Return to project root
git add buildspec-pr.yml buildspec-release.yml
git commit -m "Add CI/CD pipeline buildspec files"
git push origin main
```

## Testing Procedures

### Test 1: PR Validation Pipeline

**Trigger:** Create a pull request

```bash
# Create a test branch
git checkout -b test/pipeline-validation
echo "# Test change" >> README.md
git add README.md
git commit -m "Test CI pipeline"
git push origin test/pipeline-validation

# Create a pull request via AWS CLI
aws codecommit create-pull-request \
  --title "Test CI Pipeline" \
  --description "Testing the PR validation pipeline" \
  --targets repositoryName=redenlab-extract,sourceReference=test/pipeline-validation,destinationReference=main \
  --region us-west-2
```

**Expected behavior:**
1. EventBridge rule triggers the PR pipeline
2. CodeBuild runs `buildspec-pr.yml`
3. Executes: black check → ruff lint → mypy → tests on Python 3.8 & 3.12
4. Pipeline shows success/failure in CodePipeline console

**Monitor the pipeline:**
```bash
aws codepipeline get-pipeline-state \
  --name redenlab-extract-pr-validation \
  --region us-west-2
```

Or view in AWS Console: CodePipeline → `redenlab-extract-pr-validation`

**Check build logs:**
```bash
# Get the latest build ID
BUILD_ID=$(aws codebuild list-builds-for-project \
  --project-name redenlab-extract-pr-validation \
  --region us-west-2 \
  --query 'ids[0]' \
  --output text)

# View logs
aws codebuild batch-get-builds \
  --ids $BUILD_ID \
  --region us-west-2 \
  --query 'builds[0].logs.deepLink' \
  --output text
```

### Test 2: Release Pipeline

**Trigger:** Push a version tag

**Before tagging:**
1. Verify `__version__` in `src/redenlab_extract/__init__.py` matches the tag you'll create
2. Commit any pending changes

```bash
# Ensure you're on main branch
git checkout main
git pull origin main

# Verify version in code
python -c "from src.redenlab_extract import __version__; print(__version__)"
# Should print: 0.1.0

# Create and push a tag
git tag v0.1.0
git push origin v0.1.0
```

**Expected behavior:**
1. EventBridge rule detects tag starting with `v`
2. Release pipeline triggers
3. CodeBuild runs `buildspec-release.yml`:
   - Validates version matches tag
   - Runs quality checks
   - Tests on Python 3.8 & 3.12
   - Builds wheel and sdist
   - Publishes to PyPI
4. Package appears on PyPI: https://pypi.org/project/redenlab-extract/

**Monitor the pipeline:**
```bash
aws codepipeline get-pipeline-state \
  --name redenlab-extract-release \
  --region us-west-2
```

Or view in AWS Console: CodePipeline → `redenlab-extract-release`

**Verify PyPI publication:**
```bash
pip index versions redenlab-extract
```

### Test 3: Manual Pipeline Execution (Optional)

You can manually trigger a pipeline without waiting for events:

```bash
# Trigger PR pipeline manually
aws codepipeline start-pipeline-execution \
  --name redenlab-extract-pr-validation \
  --region us-west-2

# Trigger release pipeline manually
aws codepipeline start-pipeline-execution \
  --name redenlab-extract-release \
  --region us-west-2
```

## Troubleshooting

### Pipeline doesn't trigger on PR creation

**Check EventBridge rule:**
```bash
aws events describe-rule \
  --name redenlab-extract-pr-trigger \
  --region us-west-2
```

Ensure `State` is `ENABLED` and event pattern matches your repository.

### Build fails with "version mismatch" error

The git tag doesn't match `__version__` in code.

**Fix:**
1. Update `src/redenlab_extract/__init__.py` with the correct version
2. Commit and push
3. Delete and recreate the tag:
   ```bash
   git tag -d v0.1.0
   git push origin :refs/tags/v0.1.0
   git tag v0.1.0
   git push origin v0.1.0
   ```

### PyPI upload fails

**Check secret exists and is accessible:**
```bash
aws secretsmanager get-secret-value \
  --secret-id redenlab-extract/pypi \
  --region us-west-2
```

**Verify CodeBuild has permission:**
Check that the release build project's IAM role has `secretsmanager:GetSecretValue` permission.

### Docker permission denied in CodeBuild

Ensure `privileged: true` is set in the CodeBuild project (already configured in CDK).

## Next Steps

After successful deployment:
1. Set up branch protection rules on `main` branch
2. Require PR approval before merging
3. Consider adding Slack/email notifications for pipeline failures
4. Set up CloudWatch alarms for build failures

## Cleanup

To remove all pipeline resources:
```bash
cd cdk/
cdk destroy
```

**Note:** This will delete the pipelines but not the published PyPI packages or the Secrets Manager secret.

To delete the secret:
```bash
aws secretsmanager delete-secret \
  --secret-id redenlab-extract/pypi \
  --region us-west-2 \
  --force-delete-without-recovery
```
