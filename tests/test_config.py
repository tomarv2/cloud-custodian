# Copyright 2018 Capital One Services, LLC
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
from c7n.exceptions import PolicyValidationError
from .common import BaseTest


class ConfigRecorderTest(BaseTest):

    def test_config_recorder(self):
        factory = self.replay_flight_data('test_config_recorder')
        p = self.load_policy({
            'name': 'recorder',
            'resource': 'aws.config-recorder',
            'filters': [
                {'recordingGroup.allSupported': True},
                {'recordingGroup.includeGlobalResourceTypes': True},
                {'deliveryChannel.name': 'default'}]},
            session_factory=factory)
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['name'], 'default')


class ConfigComplianceTest(BaseTest):

    def test_config_with_inconsistent_hub_rule(self):
        factory = self.replay_flight_data('test_config_inconsistent_hub_rule')
        p = self.load_policy({
            'name': 'compliance',
            'resource': 'aws.cloudtrail',
            'filters': [
                {'type': 'config-compliance',
                 'states': ['NON_COMPLIANT'],
                 'rules': ['securityhub-cloud-trail-encryption-enabled-dadfg6']}]},
            session_factory=factory)
        resources = p.run()
        self.assertEqual(len(resources), 3)

    def test_compliance(self):
        factory = self.replay_flight_data('test_config_compliance')
        p = self.load_policy({
            'name': 'compliance',
            'resource': 'ebs',
            'filters': [
                {'type': 'config-compliance',
                 'eval_filters': [{
                     'EvaluationResultIdentifier.EvaluationResultQualifier.ResourceType': 'AWS::EC2::Volume'}], # noqa
                 'rules': ['custodian-good-vol']}
            ]}, session_factory=factory, config={'region': 'us-east-2'})
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]['VolumeId'], 'vol-0c6efd2a9f5677a03')
        self.assertEqual(resources[0]['c7n:config-compliance'][0]['Annotation'],
                         'Resource is not compliant with policy:good-vol')


class ConfigRuleTest(BaseTest):

    def test_validate(self):
        with self.assertRaises(PolicyValidationError) as ecm:
            self.load_policy({
                'name': 'rule',
                'resource': 'ebs-snapshot',
                'mode': {
                    'role': 'arn:aws:iam',
                    'type': 'config-rule'}})
        self.assertIn('AWS Config does not support resource-type:ebs-snapshot',
                      str(ecm.exception))

    def test_status(self):
        session_factory = self.replay_flight_data("test_config_rule_status")
        p = self.load_policy(
            {
                "name": "rule",
                "resource": "config-rule",
                "filters": [
                    {"type": "status", "key": "FirstEvaluationStarted", "value": True}
                ],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 3)
        self.assertEqual(
            {
                "custodian-bucket-tags",
                "custodian-bucket-ver-tags",
                "custodian-db-tags",
            },
            {r["ConfigRuleName"] for r in resources},
        )

    def test_delete(self):
        session_factory = self.replay_flight_data("test_config_rule_delete")
        p = self.load_policy(
            {
                "name": "rule",
                "resource": "config-rule",
                "filters": [{"ConfigRuleName": "custodian-db-tags"}],
                "actions": ["delete"],
            },
            session_factory=session_factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        cr = resources.pop()
        client = session_factory().client("config")
        rules = client.describe_config_rules(
            ConfigRuleNames=[cr["ConfigRuleName"]]
        ).get(
            "ConfigRules", []
        )
        self.assertEqual(rules[0]["ConfigRuleState"], "DELETING")
