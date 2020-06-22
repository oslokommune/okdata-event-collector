import pytest
import json
from event_collector.metadata_api_client import MetadataApiClient, ServerErrorException

from aws_xray_sdk.core import xray_recorder

xray_recorder.begin_segment("Test")

metadata_api_response_body = [
    {"versionID": "v123", "version": "1", "datasetID": "d123"}
]


TEST_URL = "https://test.com"


def test_version_exists(requests_mock):
    dataset_id, version = "d123", "1"

    url_with_path_params = f"{TEST_URL}/datasets/{dataset_id}/versions/{version}"

    metadata_api_client = MetadataApiClient(TEST_URL)

    requests_mock.register_uri(
        "GET",
        url_with_path_params,
        text=json.dumps(metadata_api_response_body),
        status_code=200,
    )

    version_exists = metadata_api_client.version_exists(dataset_id, version)

    assert version_exists


def test_version_exists_not_found(requests_mock):
    dataset_id, version = "d123", "1"

    url_with_path_params = f"{TEST_URL}/datasets/{dataset_id}/versions/{version}"

    metadata_api_client = MetadataApiClient(TEST_URL)

    requests_mock.register_uri(
        "GET", url_with_path_params, text="Not found", status_code=404
    )

    version_exists = metadata_api_client.version_exists(dataset_id, version)
    assert not version_exists


def test_version_exists_server_error(requests_mock):
    dataset_id, version = "d123", "1"

    url_with_path_params = f"{TEST_URL}/datasets/{dataset_id}/versions/{version}"

    metadata_api_client = MetadataApiClient(TEST_URL)

    requests_mock.register_uri(
        "GET",
        url_with_path_params,
        text=json.dumps({"message": "Server Error"}),
        status_code=500,
    )

    with pytest.raises(ServerErrorException):
        metadata_api_client.version_exists(dataset_id, version)
