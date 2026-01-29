from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_codebuild as codebuild,
)
from aws_cdk import (
    aws_codecommit as codecommit,
)
from aws_cdk import (
    aws_codepipeline as codepipeline,
)
from aws_cdk import (
    aws_codepipeline_actions as codepipeline_actions,
)
from aws_cdk import (
    aws_events as events,
)
from aws_cdk import (
    aws_events_targets as targets,
)
from aws_cdk import (
    aws_s3 as s3,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class PipelineStack(Stack):
    """
    CDK Stack for CI/CD pipeline for redenlab-extract Python package.

    Creates two pipelines:
    1. PR Validation Pipeline - Runs on pull requests (lint, test, type check)
    2. Release Pipeline - Runs on git tags (build, test, publish to PyPI)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Repository name
        repo_name = "redenlab-extract"

        # Import existing CodeCommit repository
        repository = codecommit.Repository.from_repository_name(
            self, "Repository",
            repository_name=repo_name
        )

        # S3 bucket for pipeline artifacts
        artifact_bucket = s3.Bucket(
            self, "ArtifactBucket",
            bucket_name=f"{repo_name}-pipeline-artifacts",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldArtifacts",
                    expiration=Duration.days(30),
                    enabled=True
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Reference to PyPI credentials in Secrets Manager
        pypi_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "PyPISecret",
            secret_name="redenlab-extract/pypi"
        )

        # ===== CodeBuild Projects =====

        # PR Validation Build Project
        pr_build_project = codebuild.Project(
            self, "PRValidationBuild",
            project_name=f"{repo_name}-pr-validation",
            description="Runs linting, type checking, and tests on pull requests",
            source=codebuild.Source.code_commit(repository=repository),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=True  # Required for Docker-in-Docker
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec-pr.yml"),
            cache=codebuild.Cache.bucket(artifact_bucket, prefix="cache/pr"),
            timeout=Duration.minutes(15)
        )

        # Release Build Project
        release_build_project = codebuild.Project(
            self, "ReleaseBuild",
            project_name=f"{repo_name}-release",
            description="Builds, tests, and publishes package to PyPI on tagged releases",
            source=codebuild.Source.code_commit(repository=repository),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=True  # Required for Docker-in-Docker
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec-release.yml"),
            cache=codebuild.Cache.bucket(artifact_bucket, prefix="cache/release"),
            timeout=Duration.minutes(20)
        )

        # Grant Secrets Manager read access to release build project
        pypi_secret.grant_read(release_build_project)

        # ===== PR Validation Pipeline =====

        pr_source_output = codepipeline.Artifact("PRSourceOutput")
        pr_build_output = codepipeline.Artifact("PRBuildOutput")

        pr_pipeline = codepipeline.Pipeline(
            self, "PRPipeline",
            pipeline_name=f"{repo_name}-pr-validation",
            artifact_bucket=artifact_bucket,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit",
                            repository=repository,
                            branch="master",
                            output=pr_source_output,
                            trigger=codepipeline_actions.CodeCommitTrigger.NONE  # Triggered by EventBridge
                        )
                    ]
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="ValidatePR",
                            project=pr_build_project,
                            input=pr_source_output,
                            outputs=[pr_build_output]
                        )
                    ]
                )
            ]
        )

        # ===== Release Pipeline =====

        release_source_output = codepipeline.Artifact("ReleaseSourceOutput")
        release_build_output = codepipeline.Artifact("ReleaseBuildOutput")

        release_pipeline = codepipeline.Pipeline(
            self, "ReleasePipeline",
            pipeline_name=f"{repo_name}-release",
            artifact_bucket=artifact_bucket,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit",
                            repository=repository,
                            branch="master",  # Source from master branch when tagged
                            output=release_source_output,
                            trigger=codepipeline_actions.CodeCommitTrigger.NONE  # Triggered by EventBridge
                        )
                    ]
                ),
                codepipeline.StageProps(
                    stage_name="BuildAndPublish",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="BuildTestPublish",
                            project=release_build_project,
                            input=release_source_output,
                            outputs=[release_build_output]
                        )
                    ]
                )
            ]
        )

        # ===== EventBridge Rules for Triggering Pipelines =====

        # Rule to trigger PR pipeline on pull request events
        pr_rule = events.Rule(
            self, "PREventRule",
            rule_name=f"{repo_name}-pr-trigger",
            description="Trigger PR validation pipeline on pull request creation or update",
            event_pattern=events.EventPattern(
                source=["aws.codecommit"],
                detail_type=["CodeCommit Pull Request State Change"],
                detail={
                    "event": [
                        "pullRequestCreated",
                        "pullRequestSourceBranchUpdated"
                    ],
                    "repositoryNames": [repo_name],
                    "destinationReference": ["refs/heads/master"]
                }
            )
        )
        pr_rule.add_target(targets.CodePipeline(pr_pipeline))

        # Rule to trigger release pipeline on tag creation
        release_rule = events.Rule(
            self, "ReleaseEventRule",
            rule_name=f"{repo_name}-release-trigger",
            description="Trigger release pipeline on version tag creation (v*.*.*)",
            event_pattern=events.EventPattern(
                source=["aws.codecommit"],
                detail_type=["CodeCommit Repository State Change"],
                detail={
                    "event": ["referenceCreated", "referenceUpdated"],
                    "repositoryName": [repo_name],
                    "referenceType": ["tag"],
                    "referenceName": [{"prefix": "v"}]  # Matches tags like v0.1.0, v1.0.0, etc.
                }
            )
        )
        release_rule.add_target(targets.CodePipeline(release_pipeline))
