import unittest
import boto3
import json

import python.main.handler as handler
import python.tests.test_data.event_to_record_data as event_to_record_data
import python.tests.test_data.get_failed_records_data as get_failed_records_data
from moto import mock_kinesis


class Tester(unittest.TestCase):
    def test_event_to_record_data_list(self):
        event = event_to_record_data.input_event
        record_data_list = handler.event_to_record_data_list(event)
        self.assertListEqual(record_data_list, event_to_record_data.expected)

    def test_get_failed_records(self):
        failed_records_list = handler.get_failed_records(
            get_failed_records_data.put_records_response, get_failed_records_data.record_data_list)
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


if __name__ == '__main__':
    unittest.main()
