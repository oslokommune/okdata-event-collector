import unittest
from mock import patch
import boto3
import json
from requests.exceptions import RequestException

import src.main.handler as handler
import src.tests.test_data.event_to_record_data as event_to_record_data
import src.tests.test_data.get_failed_records_data as get_failed_records_data
import src.tests.test_data.post_event_data as post_event_data
import src.tests.test_data.extract_event_body_test_data as extract_event_body_test_data
import requests_mock
from moto import mock_kinesis

class Tester(unittest.TestCase):

    get_version_url = f'{handler.metadata_api_client.url}/{post_event_data.get_metadata_route}'

    metadata_api_response_body = json.dumps([{'versionID': 'v123','version': '1','datasetID': 'd123'}])

    def test_event_to_record_list(self):
        record_list = handler.event_to_record_list(event_to_record_data.event_body)

        pairs = zip(record_list, event_to_record_data.expected)

        assert not any(x['Data'] != y['Data'] for x, y in pairs)

    def test_get_failed_records(self):
        failed_records_list = handler.get_failed_records(
            get_failed_records_data.put_records_response, get_failed_records_data.record_list)
        self.assertListEqual(failed_records_list, get_failed_records_data.expected)

    @mock_kinesis
    def test_put_records_to_kinesis(self):
        conn = boto3.client('kinesis', region_name='eu-west-1')
        stream_name = 'test_stream'
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        record_list = []
        for i in range(100):
            record_list.append({
                'PartitionKey': 'aa-bb',
                'Data': '{"data": {"key30": "value30", "key31": "value31"}, "datasetId": "d123", "version": "v123"}'
            })
        put_records_response = handler.put_records_to_kinesis(record_list, stream_name, 3)

        assert put_records_response[0]['FailedRecordCount'] == 0
        assert put_records_response[1] == []

    @mock_kinesis
    @requests_mock.Mocker(kw='mock')
    def test_post_events(self, **kwargs):
        print(self.get_version_url)
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=200)
        conn = boto3.client('kinesis', region_name='eu-west-1')
        stream_name = 'green.d123.incoming.v123.json'
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_events(post_event_data.event_with_list, None)

        self.assertDictEqual(post_event_response, post_event_data.ok_response)

    @mock_kinesis
    @requests_mock.Mocker(kw='mock')
    def test_post_single_event(self, **kwargs):
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=200)
        conn = boto3.client('kinesis', region_name='eu-west-1')
        stream_name = 'green.d123.incoming.v123.json'
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_events(post_event_data.event_with_object, None)

        self.assertDictEqual(post_event_response, post_event_data.ok_response)

    @patch('src.main.handler.put_records_to_kinesis')
    @requests_mock.Mocker(kw='request_mock')
    def test_post_evenst_failed_records(self, put_records_mock, **kwargs):
        put_records_mock.return_value = ('', post_event_data.failed_record_list)
        kwargs['request_mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=200)
        post_event_response = handler.post_events(post_event_data.event_with_list, None)
        expected_response = {
            'statusCode': 500,
            'body': '{"message": "Request failed for some elements", "failedElements": [{"key00": "value00"}, {"key10": "value10"}]}'
        }
        self.assertDictEqual(post_event_response, expected_response)

    @requests_mock.Mocker(kw='mock')
    def test_post_events_not_found(self, **kwargs):
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=404)
        post_event_response = handler.post_events(post_event_data.event_with_list, None)
        self.assertDictEqual(post_event_response, post_event_data.not_found_response)

    @requests_mock.Mocker(kw='mock')
    def test_post_events_metadata_server_error(self, **kwargs):
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=500)
        post_event_response = handler.post_events(post_event_data.event_with_list, None)
        self.assertDictEqual(post_event_response, post_event_data.error_response)

    @patch('src.main.handler.metadata_api_client.get_version')
    def test_post_events_metadata_request_exception(self, method_mock):
        method_mock.side_effect = RequestException()
        post_event_response = handler.post_events(post_event_data.event_with_list, None)
        self.assertDictEqual(post_event_response, post_event_data.error_response)

    @mock_kinesis
    @requests_mock.Mocker(kw='mock')
    def test_post_events_client_error(self, **kwargs):
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=200)
        conn = boto3.client('kinesis', region_name='eu-west-1')
        stream_name = 'green.dataset-123.incoming.version-123.json'
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_events(post_event_data.event_with_list, None)
        self.assertDictEqual(post_event_response, post_event_data.error_response)

    @requests_mock.Mocker(kw='mock')
    def test_post_events_decode_error(self, **kwargs):
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=200)
        post_event_response = handler.post_events(post_event_data.decode_error_event, None)
        self.assertDictEqual(post_event_response, post_event_data.decode_error_response)

    @requests_mock.Mocker(kw='mock')
    def test_post_events_validation_error(self, **kwargs):
        kwargs['mock'].register_uri('GET', self.get_version_url, text=self.metadata_api_response_body, status_code=200)
        post_event_response_1 = handler.post_events(post_event_data.validation_error_event_1, None)
        post_event_response_2 = handler.post_events(post_event_data.validation_error_event_2, None)
        self.assertDictEqual(post_event_response_1, post_event_data.validation_error_response)
        self.assertDictEqual(post_event_response_2, post_event_data.validation_error_response)

    def test_extract_event_body(self):
        event_body_1 = handler.extract_event_body(extract_event_body_test_data.event_with_list)
        event_body_2 = handler.extract_event_body(extract_event_body_test_data.event_with_object)
        self.assertListEqual(event_body_1, extract_event_body_test_data.expected_event_body)
        self.assertListEqual(event_body_2, extract_event_body_test_data.expected_event_body)




if __name__ == '__main__':
    unittest.main()
