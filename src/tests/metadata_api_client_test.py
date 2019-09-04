import unittest
import requests_mock
import json
from requests.exceptions import RequestException
from unittest.mock import patch
from src.main.metadata_api_client import MetadataApiClient, ServerErrorException

metadata_api_response_body = [
    {"versionID": "v123", "version": "1", "datasetID": "d123"}
]


class Tester(unittest.TestCase):

    TEST_URL = "https://test.com"

    @requests_mock.Mocker()
    def test_version_exists(self, request_mocker):
        dataset_id, version = "d123", "1"

        url_with_path_params = f"{self.TEST_URL}/datasets/{dataset_id}/versions/"

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri(
            "GET",
            url_with_path_params,
            text=json.dumps(metadata_api_response_body),
            status_code=200,
        )

        response = metadata_api_client.version_exists(dataset_id, version)

        self.assertEqual(True, response)

    @requests_mock.Mocker()
    def test_version_exists_dataset_not_found(self, request_mocker):
        dataset_id, version = "d123", "1"

        url_with_path_params = f"{self.TEST_URL}/datasets/{dataset_id}/versions/"

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri(
            "GET", url_with_path_params, text="Not found", status_code=404
        )

        response = metadata_api_client.version_exists(dataset_id, version)

        self.assertEqual(False, response)

    @requests_mock.Mocker()
    def test_version_exists_version_not_found(self, request_mocker):
        dataset_id, version_not_exist = "d123", "2"

        url_with_path_params = f"{self.TEST_URL}/datasets/{dataset_id}/versions/"

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri(
            "GET",
            url_with_path_params,
            text=json.dumps(metadata_api_response_body),
            status_code=200,
        )

        response = metadata_api_client.version_exists(dataset_id, version_not_exist)

        self.assertEqual(False, response)

    @requests_mock.Mocker()
    def test_version_exists_server_error(self, request_mocker):
        dataset_id, version = "d123", "1"

        url_with_path_params = f"{self.TEST_URL}/datasets/{dataset_id}/versions/"

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        request_mocker.register_uri(
            "GET", url_with_path_params, text="Server Error", status_code=500
        )

        with self.assertRaises(ServerErrorException):
            metadata_api_client.version_exists(dataset_id, version)

    @patch("requests.get")
    def test_version_exists_request_exception(self, get_mock):
        dataset_id, version = "d123", "1"
        get_mock.side_effect = RequestException()

        metadata_api_client = MetadataApiClient(self.TEST_URL)

        with self.assertRaises(ServerErrorException):
            metadata_api_client.version_exists(dataset_id, version)


if __name__ == "__main__":
    unittest.main()
