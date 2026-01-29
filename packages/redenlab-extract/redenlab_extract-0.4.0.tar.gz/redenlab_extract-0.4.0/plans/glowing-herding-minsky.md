# CI/CD Pipeline Implementation Plan for redenlab-extract

## Overview
Set up AWS CodePipeline with CodeBuild to automate testing, building, and publishing of the redenlab-extract Python package to PyPI.

## User Requirements
- **Publish to**: PyPI (public)
- **Triggers**: Pull requests + Tagged releases (v*.*.*)
- **Python versions**: Test on 3.8 (min) and 3.12 (max)
- **Versioning**: Manual (no auto-bumping)

## Architecture

### Two-Pipeline Approach
1. **PR Validation Pipeline** - Fast feedback on pull requests (lint, test, type check)
2. **Release Pipeline** - Full validation + build + publish to PyPI on git tags

## Implementation Steps

### 1. Create buildspec-pr.yml
**Location**: `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/buildspec-pr.yml`

**Purpose**: CodeBuild specification for PR validation

**Key phases**:
- **install**: Install Python 3.12 + pip dependencies
- **pre_build**: Run black, ruff, mypy checks (fail fast)
- **build**: Test on Python 3.8 (via Docker) and Python 3.12 (native)
- **post_build**: Report results

**Features**:
- Docker-in-Docker for Python 3.8 testing
- Coverage report generation
- Pip dependency caching

### 2. Create buildspec-release.yml
**Location**: `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/buildspec-release.yml`

**Purpose**: CodeBuild specification for releases

**Key phases**:
- **install**: Install Python 3.12 + build tools (build, twine)
- **pre_build**: Run quality checks + validate version matches git tag
- **build**: Test on Python 3.8 & 3.12 + build wheel/sdist
- **post_build**: Publish to PyPI using Secrets Manager credentials

**Features**:
- Version validation (tag vs `__version__`)
- Package validation via twine
- Secure PyPI credential retrieval from AWS Secrets Manager
- Artifact archival

### 3. Create CDK Infrastructure (Python)
**Location**: `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/cdk/`

**Purpose**: Infrastructure as code using AWS CDK for Python

**Project Structure**:
```
cdk/
├── app.py                    # CDK app entry point
├── cdk.json                  # CDK configuration
├── requirements.txt          # CDK dependencies
└── pipeline_stack.py         # Main stack definition
```

**CDK Stack Components** (in `pipeline_stack.py`):
1. **S3 Artifact Bucket** - Store build artifacts (30-day lifecycle)
2. **IAM Roles**:
   - CodePipeline service role
   - CodeBuild PR role (no secrets access)
   - CodeBuild release role (with Secrets Manager access)
   - CloudWatch Events role
3. **CodeBuild Projects**:
   - `redenlab-extract-pr-validation` (uses buildspec-pr.yml)
   - `redenlab-extract-release` (uses buildspec-release.yml)
   - Both use `aws/codebuild/standard:7.0` image with privileged mode
4. **CodePipeline Pipelines**:
   - PR pipeline (Source → Build)
   - Release pipeline (Source → Build+Publish)
5. **CloudWatch Event Rules**:
   - PR events trigger (pullRequestCreated, pullRequestSourceBranchUpdated)
   - Tag push trigger (tags matching `v*`)

**Configuration**:
- Compute: BUILD_GENERAL1_SMALL (cost-effective)
- Region: us-west-2 (matches CodeCommit)
- Cache: S3-based pip cache
- CDK Version: v2 (latest)

**Key CDK Constructs**:
- `aws_s3.Bucket` for artifact storage
- `aws_codebuild.Project` for build projects
- `aws_codepipeline.Pipeline` for pipelines
- `aws_events.Rule` for triggers
- `aws_iam.Role` for permissions

### 4. Create Setup Documentation
**Location**: `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/docs/cicd-setup.md`

**Content**:
- Prerequisites (AWS credentials, PyPI token)
- Step-by-step deployment instructions
- Testing procedures
- Troubleshooting guide
- Cost estimates

### 5. Update .gitignore
**Location**: `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/.gitignore`

**Add**: CDK deployment artifacts:
- `cdk.out/` - CDK synthesized CloudFormation templates
- `cdk/.venv/` - CDK virtual environment (if created locally)

## Pre-Deployment Requirements

### 1. Store PyPI Credentials
```bash
aws secretsmanager create-secret \
  --name redenlab-extract/pypi \
  --secret-string '{"username":"__token__","password":"pypi-AgE..."}' \
  --region us-west-2
```

### 2. Ensure `__version__` exists
**File**: `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/src/redenlab_extract/__init__.py`

Must contain `__version__ = "0.1.0"` for version validation to work.

## Deployment Steps

1. **Install CDK CLI** (if not already installed):
   ```bash
   npm install -g aws-cdk
   ```

2. **Bootstrap CDK** (one-time per account/region):
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/us-west-2
   ```

3. **Install CDK dependencies**:
   ```bash
   cd cdk/
   pip install -r requirements.txt
   ```

4. **Synthesize and review CloudFormation template**:
   ```bash
   cdk synth
   ```

5. **Deploy the CDK stack**:
   ```bash
   cdk deploy --require-approval never
   ```

6. **Commit and push buildspec files**:
   ```bash
   cd ..
   git add buildspec-pr.yml buildspec-release.yml cdk/
   git commit -m "Add CI/CD pipeline configuration with CDK"
   git push origin main
   ```

7. **Test PR pipeline**: Create a test PR
8. **Test release pipeline**: Push a tag (`git tag v0.1.0 && git push origin v0.1.0`)

## Key Design Decisions

1. **AWS CDK over CloudFormation**: Use CDK for type safety, less code (~150 lines vs ~400), and better maintainability with Python constructs

2. **Docker for multi-Python testing**: Use Docker containers within CodeBuild for Python 3.8 testing (CodeBuild standard:7.0 has Python 3.12 natively)

3. **Secrets Manager for PyPI**: Secure credential storage with IAM-based access control

4. **Separate pipelines**: PR validation (fast) vs Release publishing (comprehensive) for different use cases

5. **Version validation**: Prevent version mismatches by validating git tag matches `__version__` before publishing

6. **S3 caching**: Cache pip dependencies to speed up builds

## Files to Create

1. `buildspec-pr.yml` - PR validation build spec (~50 lines)
2. `buildspec-release.yml` - Release build spec (~80 lines)
3. `cdk/app.py` - CDK app entry point (~20 lines)
4. `cdk/pipeline_stack.py` - Main CDK stack (~150 lines)
5. `cdk/cdk.json` - CDK configuration (~15 lines)
6. `cdk/requirements.txt` - CDK dependencies (~5 lines)
7. `docs/cicd-setup.md` - Setup documentation (~200 lines)

## Files to Verify (not modify)

1. `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/pyproject.toml` - Build configuration
2. `/Users/ayushranjan/Documents/Redenlab/Git_projects/redenlab-extract/src/redenlab_extract/__init__.py` - Should contain `__version__`

## Testing Strategy

### PR Pipeline (~4-5 minutes)
- Code quality checks (30s)
- Python 3.8 tests (2-3 min)
- Python 3.12 tests (1-2 min)

### Release Pipeline (~5-6 minutes)
- All PR checks
- Version validation
- Package building
- PyPI publishing

## Cost Estimate
- **~$4-5/month** for 50 PRs + 4 releases/month
- Breakdown: CodeBuild ($1.40), CodePipeline ($2), S3 ($0.25), Secrets Manager ($0.40), Logs ($0.25)

## Security Measures
- PyPI credentials in Secrets Manager (encrypted)
- IAM least privilege (separate roles for PR vs release)
- S3 artifacts encrypted at rest
- No public access to artifacts
- CloudTrail logging for secret access

## Future Enhancements (out of scope)
- Test all Python versions 3.8-3.12
- Security scanning (Snyk/Safety)
- Test PyPI staging environment
- Automated changelog generation
- Slack/email notifications
