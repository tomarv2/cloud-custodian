# Copyright 2016-2017 Capital One Services, LLC
# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
from .common import BaseTest


class Kinesis(BaseTest):

    def test_stream_query(self):
        factory = self.replay_flight_data("test_kinesis_stream_query")
        p = self.load_policy(
            {
                "name": "kstream",
                "resource": "kinesis",
                "filters": [
                    {"type": "value", "value_type": "size", "value": 3, "key": "Shards"}
                ],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["Tags"], [{"Key": "Origin", "Value": "home"}])
        self.assertEqual(resources[0]["StreamStatus"], "ACTIVE")

    def test_stream_delete(self):
        factory = self.replay_flight_data("test_kinesis_stream_delete")
        p = self.load_policy(
            {
                "name": "kstream",
                "resource": "kinesis",
                "filters": [{"StreamName": "sock-drawer"}],
                "actions": ["delete"],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        stream = factory().client("kinesis").describe_stream(StreamName="sock-drawer")[
            "StreamDescription"
        ]
        self.assertEqual(stream["StreamStatus"], "DELETING")

    def test_stream_encrypt(self):
        factory = self.replay_flight_data("test_kinesis_encrypt")
        p = self.load_policy(
            {
                "name": "kstream",
                "resource": "kinesis",
                "filters": [{"StreamName": "sock-drawer"}],
                "actions": [{"type": "encrypt", "key": "aws/kinesis"}],
            },
            session_factory=factory,
        )
        p.run()
        stream = factory().client("kinesis").describe_stream(StreamName="sock-drawer")[
            "StreamDescription"
        ]
        self.assertEqual(stream["EncryptionType"], "KMS")

    def test_hose_query(self):
        factory = self.replay_flight_data("test_kinesis_hose_query")
        p = self.load_policy(
            {
                "name": "khole",
                "resource": "firehose",
                "filters": [{"DeliveryStreamName": "sock-index-hose"}],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["DeliveryStreamStatus"], "ACTIVE")

    def test_firehose_delete(self):
        factory = self.replay_flight_data("test_kinesis_hose_delete")
        p = self.load_policy(
            {
                "name": "khole",
                "resource": "firehose",
                "filters": [{"DeliveryStreamName": "sock-index-hose"}],
                "actions": ["delete"]
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(
            factory().client("firehose").describe_delivery_stream(
                DeliveryStreamName="sock-index-hose"
            )[
                "DeliveryStreamDescription"
            ][
                "DeliveryStreamStatus"
            ],
            "DELETING",
        )

    def test_firehose_extended_s3_encrypt_s3_destination(self):
        factory = self.replay_flight_data("test_firehose_ext_s3_encrypt_s3_destination")
        p = self.load_policy(
            {
                "name": "khole",
                "resource": "firehose",
                "filters": [{"type": "value",
                    "key": "Destinations[0].S3DestinationDescription.EncryptionConfiguration.NoEncryptionConfig",  # noqa: E501
                             "value": "present"}],
                "actions": [{"type": "encrypt-s3-destination",
                             "key_arn": "arn:aws:kms:us-east-1:123456789:alias/aws/s3"}],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        s = factory().client("firehose").describe_delivery_stream(
            DeliveryStreamName="firehose-s3"
        )['DeliveryStreamDescription']['Destinations'][0]
        assert 'KMSEncryptionConfig' in s['S3DestinationDescription']['EncryptionConfiguration'].keys()  # noqa: E501

    def test_firehose_splunk_encrypt_s3_destination(self):
        factory = self.replay_flight_data("test_firehose_splunk_encrypt_s3_destination")
        p = self.load_policy(
            {
                "name": "khole",
                "resource": "firehose",
                "filters": [{"type": "value",
                    "key": "Destinations[0].SplunkDestinationDescription.S3DestinationDescription.EncryptionConfiguration.NoEncryptionConfig",  # noqa: E501
                             "value": "present"}],
                "actions": [{"type": "encrypt-s3-destination",
                             "key_arn": "arn:aws:kms:us-east-1:123456789:alias/aws/s3"}],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        s = factory().client("firehose").describe_delivery_stream(
            DeliveryStreamName="firehose-splunk"
        )['DeliveryStreamDescription']['Destinations'][0]['SplunkDestinationDescription']
        assert 'KMSEncryptionConfig' in \
            s['S3DestinationDescription']['EncryptionConfiguration'].keys()

    def test_firehose_elasticsearch_encrypt_s3_destination(self):
        factory = self.replay_flight_data("test_firehose_elasticsearch_encrypt_s3_destination")
        p = self.load_policy(
            {
                "name": "khole",
                "resource": "firehose",
                "filters": [{"type": "value",
                    "key": "Destinations[0].ElasticsearchDestinationDescription.S3DestinationDescription.EncryptionConfiguration.NoEncryptionConfig",  # noqa: E501
                             "value": "present"}],
                "actions": [{"type": "encrypt-s3-destination",
                             "key_arn": "arn:aws:kms:us-east-1:123456789:alias/aws/s3"}],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        s = factory().client("firehose").describe_delivery_stream(
            DeliveryStreamName="firehose-splunk"
        )['DeliveryStreamDescription']['Destinations'][0]['ElasticsearchDestinationDescription']
        assert 'KMSEncryptionConfig' in \
            s['S3DestinationDescription']['EncryptionConfiguration'].keys()

    def test_firehose_redshift_encrypt_s3_destination(self):
        factory = self.replay_flight_data("test_firehose_redshift_encrypt_s3_destination")
        p = self.load_policy(
            {
                "name": "khole",
                "resource": "firehose",
                "filters": [{"type": "value",
                    "key": "Destinations[0].RedshiftDestinationDescription.S3DestinationDescription.EncryptionConfiguration.NoEncryptionConfig",  # noqa: E501
                             "value": "present"}],
                "actions": [{"type": "encrypt-s3-destination",
                             "key_arn": "arn:aws:kms:us-east-1:123456789:alias/aws/s3"}],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        s = factory().client("firehose").describe_delivery_stream(
            DeliveryStreamName="firehose-redshift"
        )['DeliveryStreamDescription']['Destinations'][0]['RedshiftDestinationDescription']
        assert 'KMSEncryptionConfig' in \
            s['S3DestinationDescription']['EncryptionConfiguration'].keys()

    def test_app_query(self):
        factory = self.replay_flight_data("test_kinesis_analytics_query")
        p = self.load_policy(
            {
                "name": "kapp",
                "resource": "kinesis-analytics",
                "filters": [{"ApplicationStatus": "RUNNING"}],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["ApplicationName"], "sock-app")

    def test_app_delete(self):
        factory = self.replay_flight_data("test_kinesis_analytics_delete")
        p = self.load_policy(
            {
                "name": "kapp",
                "resource": "kinesis-analytics",
                "filters": [{"ApplicationName": "sock-app"}],
                "actions": ["delete"],
            },
            session_factory=factory,
        )
        resources = p.run()
        self.assertEqual(len(resources), 1)
        self.assertEqual(
            factory().client("kinesisanalytics").describe_application(
                ApplicationName="sock-app"
            )[
                "ApplicationDetail"
            ][
                "ApplicationStatus"
            ],
            "DELETING",
        )
