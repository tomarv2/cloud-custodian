# Copyright 2017 Capital One Services, LLC
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
import time
from .common import BaseTest

from c7n.resources.aws import shape_validate


class CodeCommit(BaseTest):

    def test_query_repos(self):
        factory = self.replay_flight_data("test_codecommit")
        p = self.load_policy(
            {"name": "get-repos", "resource": "codecommit"}, session_factory=factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(
            resources[0]["cloneUrlSsh"],
            "ssh://git-codecommit.us-east-2.amazonaws.com/v1/repos/custodian-config-repo",
        )

    def test_get_repo_resources(self):
        factory = self.replay_flight_data('test_codecommit_get')
        p = self.load_policy({
            'name': 'get-repos', 'resource': 'codecommit'},
            session_factory=factory)
        m = p.resource_manager
        resources = m.get_resources(['fizzbuzz'])
        self.assertEqual(len(resources), 1)
        r = resources.pop()
        self.assertEqual(r['repositoryName'], 'fizzbuzz')

    def test_delete_repos(self):
        factory = self.replay_flight_data("test_codecommit_delete")
        p = self.load_policy(
            {
                "name": "delete-repos",
                "resource": "codecommit",
                "filters": [{"repositoryDescription": "placebo"}],
                "actions": ["delete"],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 2)
        self.assertEqual(
            sorted([r["repositoryName"] for r in resources]),
            ["test-delete-codecommit", "test-delete-codecommit3"],
        )
        client = factory().client("codecommit")
        remainder = client.list_repositories()["repositories"]
        self.assertEqual(len(remainder), 1)
        self.assertNotEqual(remainder[0]["repositoryName"], "test-delete-codecommit")
        self.assertNotEqual(remainder[0]["repositoryName"], "test-delete-codecommit3")


class CodeBuild(BaseTest):

    def test_query_builds(self):
        factory = self.replay_flight_data("test_codebuild")
        p = self.load_policy(
            {"name": "get-builders", "resource": "codebuild"}, session_factory=factory
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)

        self.assertEqual(
            resources[0]["environment"],
            {
                u"computeType": u"BUILD_GENERAL1_SMALL",
                u"environmentVariables": [],
                u"image": u"aws/codebuild/python:2.7.12",
                u"type": u"LINUX_CONTAINER",
            },
        )

    def test_delete_builds(self):
        factory = self.replay_flight_data("test_codebuild_delete")
        p = self.load_policy(
            {
                "name": "delete-builders",
                "resource": "codebuild",
                "filters": [{"description": "placebo"}],
                "actions": ["delete"],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["name"], "test-delete-codebuild")
        client = factory().client("codebuild")
        remainder = client.list_projects()["projects"]
        self.assertEqual(len(remainder), 2)
        self.assertNotIn("test-delete-codebuild", remainder)

    def test_post_finding_build(self):
        factory = self.replay_flight_data('test_codebuild_post_finding')
        p = self.load_policy({
            'name': 'codebuild',
            'resource': 'aws.codebuild',
            'actions': [
                {'type': 'post-finding',
                 'types': [
                     'Software and Configuration Checks/OrgStandard/abc-123']}]},
            session_factory=factory, config={'region': 'us-east-2'})
        builds = p.resource_manager.resources()
        self.assertEqual(len(builds), 1)
        self.maxDiff = None
        rfinding = p.resource_manager.actions[0].format_resource(builds[0])
        self.assertEqual(
            rfinding,
            {'Details': {
                'AwsCodeBuildProject': {
                    'EncryptionKey': 'arn:aws:kms:us-east-2:644160558196:alias/aws/s3',
                    'Environment': {'ImagePullCredentialsType': 'CODEBUILD',
                                    'Type': 'LINUX_CONTAINER'},
                    'Name': 'custodian',
                    'ServiceRole': 'arn:aws:iam::644160558196:role/service-role/codebuild-test-service-role',  # noqa
                    'Source': {'Location': 'https://github.com/kapilt/cloud-custodian',
                               'Type': 'GITHUB'}}},
             'Id': 'arn:aws:codebuild:us-east-2:644160558196:project/custodian',
             'Partition': 'aws',
             'Region': 'us-east-2',
             'Type': 'AwsCodeBuildProject'})

        shape_validate(
            rfinding['Details']['AwsCodeBuildProject'],
            'AwsCodeBuildProjectDetails',
            'securityhub')


class CodePipeline(BaseTest):

    def test_query_pipeline(self):
        factory = self.replay_flight_data("test_codepipeline")
        p = self.load_policy(
            {"name": "get-pipes", "resource": "codepipeline"},
            session_factory=factory, config={'account_id': '001100'},
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(
            p.resource_manager.get_arns(resources),
            ['arn:aws:codepipeline:us-east-1:001100:custodian-deploy'])
        self.assertEqual(len(resources[0]["stages"]), 2)

    def test_delete_pipeline(self):
        factory = self.replay_flight_data('test_codepipeline_delete')
        p = self.load_policy(
            {'name': 'del-pipe', 'resource': 'aws.codepipeline',
             'actions': ['delete']},
            session_factory=factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        client = factory().client('codepipeline')
        if self.recording:
            time.sleep(2)
        self.assertFalse(client.list_pipelines().get('pipelines'))
