import unittest
import json
import requests_mock

from src.main.metadata_api_client import *

metadata_api_response_body = [
    {
        'versionID': 'v123',
        'version': '1',
        'datasetID': 'd123'
    }
]

class Tester(unittest.TestCase):

    TEST_URL = 'https://test.com'

    @requests_mock.Mocker()
    def test_get_version(self, request_mocker):
        dataset_id, version_id = 'd123', 'v123'

        url_with_path_params = f'{self.TEST_URL}/datasets/{dataset_id}/versions/{version_id}'

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri('GET', url_with_path_params, text=json.dumps(metadata_api_response_body), status_code=200)

        response = metadata_api_client.get_version(dataset_id, version_id)

        self.assertListEqual(metadata_api_response_body, response)

    @requests_mock.Mocker()
    def test_get_version_not_found(self, request_mocker):
        dataset_id, version_id = 'd123', 'v123'

        url_with_path_params = f'{self.TEST_URL}/datasets/{dataset_id}/versions/{version_id}'

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri('GET', url_with_path_params, text="Not found", status_code=404)

        with self.assertRaises(NotFoundException):
            metadata_api_client.get_version(dataset_id, version_id)

    @requests_mock.Mocker()
    def test_get_version_server_error(self, request_mocker):
        dataset_id, version_id = 'd123', 'v123'

        url_with_path_params = f'{self.TEST_URL}/datasets/{dataset_id}/versions/{version_id}'

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri('GET', url_with_path_params, text="Not found", status_code=500)

        with self.assertRaises(ServerErrorException):
            metadata_api_client.get_version(dataset_id, version_id)


if __name__ == '__main__':
    unittest.main()
