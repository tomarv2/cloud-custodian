# Copyright 2019 Capital One Services, LLC
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
import time

from gcp_common import BaseTest


class DMDeploymentTest(BaseTest):
    def test_deployment_query(self):
        project_id = 'mitraject'
        session_factory = self.replay_flight_data('dm-deployment-query', project_id=project_id)

        policy = {
            'name': 'all-deployments',
            'resource': 'gcp.dm-deployment'
        }

        policy = self.load_policy(
            policy,
            session_factory=session_factory)

        resources = policy.run()
        self.assertEqual(resources[0]['name'], 'mydep2')

    def test_deployment_get(self):
        project_id = 'mitraject'
        session_factory = self.replay_flight_data('dm-deployment-get', project_id=project_id)

        policy = {
            'name': 'one-deployment',
            'resource': 'gcp.dm-deployment'
        }

        policy = self.load_policy(
            policy,
            session_factory=session_factory)

        deployment = policy.resource_manager.get_resource({
            'project_id': project_id,
            'name': 'mydep2'
        })

        self.assertEqual(deployment['id'], '7713223424225049872')

    def test_deployment_delete(self):
        project_id = 'mitrop-custodian'
        factory = self.replay_flight_data('dm-deployment-delete', project_id=project_id)

        p = self.load_policy(
            {'name': 'delete-deployment',
             'resource': 'gcp.dm-deployment',
             'filters': [{'name': 'lamp-1'}],
             'actions': ['delete']},
            session_factory=factory)

        resources = p.run()
        self.assertEqual(len(resources), 1)

        if self.recording:
            time.sleep(3)

        client = p.resource_manager.get_client()
        result = client.execute_query(
            'list', {'project': project_id,
                     'filter': 'name = lamp-1'})

        self.assertEqual(result['deployments'][0]['operation']['operationType'], 'delete')
