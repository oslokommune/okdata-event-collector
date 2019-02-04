import unittest
import boto3
import json

import python.main.handler as handler
import python.tests.test_data.event_to_record_data as event_to_record_data
from moto import mock_kinesis


class Tester(unittest.TestCase):

    def test_event_to_record_data_list(self):
        event = event_to_record_data.input_event
        record_data_list = handler.event_to_record_data_list(event)
        print(record_data_list)
        self.assertListEqual(record_data_list, event_to_record_data.expected)

    # @mock_kinesis
    # def test_post_record(self):
    #     assert True


if __name__ == '__main__':
    unittest.main()