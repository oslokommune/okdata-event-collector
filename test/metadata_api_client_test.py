import pytest
import json
from event_collector.metadata_api_client import (
    MetadataApiClient,
    ServerErrorException,
    version_exists,
    get_confidentiality,
)

from aws_xray_sdk.core import xray_recorder

xray_recorder.begin_segment("Test")

dataset = {
    "Id": "d123",
    "accessRights": "public",
    "_embedded": {"versions": [{"version": "1"}]},
}


TEST_URL = "https://test.com"


def test_get_dataset_and_versions(requests_mock):
    dataset_id, version = "d123", "1"
    url_with_path_params = f"{TEST_URL}/datasets/{dataset_id}"

    metadata_api_client = MetadataApiClient(TEST_URL)

    requests_mock.register_uri(
        "GET",
        url_with_path_params,
        text=json.dumps(dataset),
        status_code=200,
    )

    assert metadata_api_client.get_dataset_and_versions(dataset_id) == dataset
    assert version_exists(dataset, version)
    assert not version_exists(dataset, "2")
    assert get_confidentiality(dataset) == "green"


def test_get_dataset_and_versions_not_found(requests_mock):
    dataset_id = "d123"

    url_with_path_params = f"{TEST_URL}/datasets/{dataset_id}"

    metadata_api_client = MetadataApiClient(TEST_URL)

    requests_mock.register_uri(
        "GET", url_with_path_params, text="Not found", status_code=404
    )

    dataset = metadata_api_client.get_dataset_and_versions(dataset_id)
    assert not dataset


def test_version_exists_server_error(requests_mock):
    dataset_id = "d123"

    url_with_path_params = f"{TEST_URL}/datasets/{dataset_id}"

    metadata_api_client = MetadataApiClient(TEST_URL)

    requests_mock.register_uri(
        "GET",
        url_with_path_params,
        text=json.dumps({"message": "Server Error"}),
        status_code=500,
    )

    with pytest.raises(ServerErrorException):
        metadata_api_client.get_dataset_and_versions(dataset_id)
