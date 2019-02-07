import unittest
from mock import patch
import boto3
import json

import src.main.handler as handler
import src.tests.test_data.event_to_record_data as event_to_record_data
import src.tests.test_data.get_failed_records_data as get_failed_records_data
import src.tests.test_data.post_event_data as post_event_data
from moto import mock_kinesis


class Tester(unittest.TestCase):
    def test_event_to_record_list(self):
        event = event_to_record_data.input_event
        record_list = handler.event_to_record_list(event)

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
    def test_post_event(self):
        conn = boto3.client('kinesis', region_name='eu-west-1')
        stream_name = 'green.d123.incoming.v123.json'
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_event(post_event_data.event, None)

        self.assertDictEqual(post_event_response, post_event_data.ok_response)

    @patch('src.main.handler.put_records_to_kinesis')
    def test_post_event_failed_records(self, put_records_to_kinesis_patch):
        put_records_to_kinesis_patch.return_value = ('', post_event_data.failed_record_list)
        post_event_response = handler.post_event(post_event_data.event, None)
        expected_response = {
            'statusCode': 500,
            'body': '{"message": "Request failed for some elements", "failedElements": [{"key00": "value00"}, {"key10": "value10"}]}'
        }
        self.assertDictEqual(post_event_response, expected_response)

    def test_post_event_not_found(self):
        post_event_response = handler.post_event(post_event_data.event_not_found, None)
        self.assertDictEqual(post_event_response, post_event_data.not_found_response)

    @mock_kinesis
    def test_post_event_client_error(self):
        conn = boto3.client('kinesis', region_name='eu-west-1')
        stream_name = 'green.d123.incoming.v123.json'
        conn.create_stream(StreamName=stream_name, ShardCount=1)
        post_event_response = handler.post_event(post_event_data.client_error_event, None)
        self.assertDictEqual(post_event_response, post_event_data.error_response)

    def test_post_event_decode_error(self):
        post_event_response = handler.post_event(post_event_data.decode_error_event, None)
        self.assertDictEqual(post_event_response, post_event_data.decode_error_response)

    def test_post_event_validation_error(self):
        post_event_response_1 = handler.post_event(post_event_data.validation_error_event_1, None)
        post_event_response_2 = handler.post_event(post_event_data.validation_error_event_2, None)
        self.assertDictEqual(post_event_response_1, post_event_data.validation_error_response)
        self.assertDictEqual(post_event_response_2, post_event_data.validation_error_response)



if __name__ == '__main__':
    unittest.main()
