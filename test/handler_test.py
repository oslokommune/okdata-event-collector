import unittest
from mock import patch
import boto3
import json
from auth import SimpleAuth
import event_collector.handler as handler
import test.test_data.event_to_record_data as event_to_record_data
import test.test_data.get_failed_records_data as get_failed_records_data
import test.test_data.post_event_data as post_event_data
import test.test_data.extract_event_body_test_data as extract_event_body_test_data
import requests_mock
from moto import mock_kinesis


from aws_xray_sdk.core import xray_recorder

xray_recorder.begin_segment("Test")


def mock_auth(mock, access):
    mock.register_uri(
        "GET",
        f"https://example.com/{post_event_data.datasetId}",
        text=json.dumps({"access": access}),
        status_code=200,
    )


def mock_get_confidentiality(requests_mocker, dataset_id, conf):
    requests_mocker.register_uri(
        "GET",
        f"{handler.metadata_api_client.url}/datasets/{dataset_id}",
        text=json.dumps({"confidentiality": conf}),
        status_code=200,
    )


class Tester(unittest.TestCase):

    get_version_url = f"{handler.metadata_api_client.url}/{post_event_data.get_dataset_versions_route}"
    get_dataset_url = f"{handler.metadata_api_client.url}/{post_event_data.get_dataset_versions_route}"

    metadata_api_response_body = json.dumps(
        [{"versionID": "v123", "version": "1", "datasetID": "d123"}]
    )

    def test_event_to_record_list(self):
        record_list = handler.event_to_record_list(event_to_record_data.event_body)

        pairs = zip(record_list, event_to_record_data.expected)

        assert not any(x["Data"] != y["Data"] for x, y in pairs)

    def test_get_failed_records(self):
        failed_records_list = handler.get_failed_records(
            get_failed_records_data.put_records_response,
            get_failed_records_data.record_list,
        )
        self.assertListEqual(failed_records_list, get_failed_records_data.expected)

    @mock_kinesis
    def test_put_records_to_kinesis(self):
        conn = boto3.client("kinesis", region_name="eu-west-1")
        stream_name = "test_stream"
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        record_list = []
        for i in range(100):
            record_list.append(
                {
                    "PartitionKey": "aa-bb",
                    "Data": '{"data": {"key30": "value30", "key31": "value31"}, "datasetId": "d123", "version": "1"}',
                }
            )
        put_records_response = handler.put_records_to_kinesis(
            record_list, stream_name, 3
        )

        assert put_records_response[0]["FailedRecordCount"] == 0
        assert put_records_response[1] == []

    @mock_kinesis
    @requests_mock.Mocker()
    def test_post_events(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )
        mock_get_confidentiality(request_mocker, "d123", "green")
        conn = boto3.client("kinesis", region_name="eu-west-1")
        stream_name = "dp.green.d123.incoming.1.json"
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_events(post_event_data.event_with_list, {})

        self.assertDictEqual(post_event_response, post_event_data.ok_response)

    @mock_kinesis
    @requests_mock.Mocker()
    def test_post_single_event(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )
        mock_get_confidentiality(request_mocker, "d123", "yellow")
        conn = boto3.client("kinesis", region_name="eu-west-1")
        stream_name = "dp.yellow.d123.incoming.1.json"
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_events(post_event_data.event_with_object, {})

        self.assertDictEqual(post_event_response, post_event_data.ok_response)

    @patch("event_collector.handler.put_records_to_kinesis")
    @requests_mock.Mocker()
    def test_post_evenst_failed_records(self, put_records_mock, request_mocker):
        mock_auth(request_mocker, access=True)
        put_records_mock.return_value = ("", post_event_data.failed_record_list)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )
        mock_get_confidentiality(request_mocker, "d123", "green")
        post_event_response = handler.post_events(post_event_data.event_with_list, {})
        expected_response = {
            "statusCode": 500,
            "body": '{"message": "Request failed for some elements", "failedElements": [{"key00": "value00"}, {"key10": "value10"}]}',
        }
        self.assertDictEqual(post_event_response, expected_response)

    @requests_mock.Mocker()
    def test_post_events_not_found(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=404,
        )
        post_event_response = handler.post_events(post_event_data.event_with_list, {})
        self.assertDictEqual(post_event_response, post_event_data.not_found_response)

    @requests_mock.Mocker()
    def test_post_events_metadata_server_error(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=500,
        )
        post_event_response = handler.post_events(post_event_data.event_with_list, {})
        self.assertDictEqual(post_event_response, post_event_data.error_response)

    @mock_kinesis
    @requests_mock.Mocker()
    def test_post_events_client_error(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )
        mock_get_confidentiality(request_mocker, "d123", "green")
        conn = boto3.client("kinesis", region_name="eu-west-1")
        stream_name = "dp.green.dataset-123.incoming.version-123.json"
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_events(post_event_data.event_with_list, {})
        self.assertDictEqual(post_event_response, post_event_data.error_response)

    @requests_mock.Mocker()
    def test_post_events_decode_error(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )
        post_event_response = handler.post_events(
            post_event_data.decode_error_event, {}
        )
        self.assertDictEqual(post_event_response, post_event_data.decode_error_response)

    @requests_mock.Mocker()
    def test_post_events_validation_error(self, request_mocker):
        mock_auth(request_mocker, access=True)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )
        post_event_response_1 = handler.post_events(
            post_event_data.validation_error_event_1, {}
        )
        post_event_response_2 = handler.post_events(
            post_event_data.validation_error_event_2, {}
        )
        self.assertDictEqual(
            post_event_response_1, post_event_data.validation_error_response
        )
        self.assertDictEqual(
            post_event_response_2, post_event_data.validation_error_response
        )

    @requests_mock.Mocker()
    def test_post_events_forbidden(self, request_mocker):
        mock_auth(request_mocker, access=False)
        request_mocker.register_uri(
            "GET",
            self.get_version_url,
            text=self.metadata_api_response_body,
            status_code=200,
        )

        response = handler.post_events(post_event_data.event_with_object, {})

        self.assertEqual(response, post_event_data.forbidden_response)

    def test_extract_event_body(self):
        event_body_1 = handler.extract_event_body(
            extract_event_body_test_data.event_with_list
        )
        event_body_2 = handler.extract_event_body(
            extract_event_body_test_data.event_with_object
        )
        self.assertListEqual(
            event_body_1, extract_event_body_test_data.expected_event_body
        )
        self.assertListEqual(
            event_body_2, extract_event_body_test_data.expected_event_body
        )

    @patch.object(SimpleAuth, "webhook_token_is_authorized")
    def test_post_events_webhook_auth_forbidden(self, auth_mock):
        access_denied_token = "access-denied-token"

        auth_mock.return_value = False, "Forbidden"

        event_access_denied = {
            "pathParameters": {"dataset_id": "datasetId", "version": "version"},
            "queryStringParameters": {"token": access_denied_token},
            "body": '{"kake": "parmesan"}',
        }

        forbidden_response = handler.events_webhook(event_access_denied, {})
        assert forbidden_response["statusCode"] == 403
        assert forbidden_response["body"] == '{"message": "Forbidden"}'


if __name__ == "__main__":
    unittest.main()
