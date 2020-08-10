# Copyright 2015-2018 Capital One Services, LLC
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
from ..azure_common import BaseTest, arm_template


class CdnTest(BaseTest):
    def setUp(self):
        super(CdnTest, self).setUp()

    def test_cdn_schema_validate(self):
        with self.sign_out_patch():
            p = self.load_policy({
                'name': 'test-azure-cdn',
                'resource': 'azure.cdnprofile'
            }, validate=True)
            self.assertTrue(p)

    @arm_template('cdnprofile.json')
    def test_find_profile_by_name(self):
        p = self.load_policy({
            'name': 'test-azure-cdnprofile',
            'resource': 'azure.cdnprofile',
            'filters': [
                {'type': 'value',
                 'key': 'name',
                 'op': 'eq',
                 'value_type': 'normalize',
                 'value': 'cctestcdnprofile'}],
        })
        resources = p.run()
        self.assertEqual(len(resources), 1)
