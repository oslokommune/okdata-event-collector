import json

import pytest
from aws_xray_sdk.core import xray_recorder
from moto import mock_kinesis, mock_dynamodb2

from okdata.resource_auth import ResourceAuthorizer

import event_collector.handler as handler
import test.test_data.event_to_record_data as event_to_record_data
import test.test_data.extract_event_body_test_data as extract_event_body_test_data
import test.test_data.get_failed_records_data as get_failed_records_data
import test.test_data.post_event_data as post_event_data
from test.test_utils import create_event_stream, create_event_streams_table

xray_recorder.begin_segment("Test")


def test_event_to_record_list():
    record_list = handler.event_to_record_list(event_to_record_data.event_body)
    pairs = zip(record_list, event_to_record_data.expected)
    assert not any(x["Data"] != y["Data"] for x, y in pairs)


def test_get_failed_records():
    failed_records_list = handler.get_failed_records(
        get_failed_records_data.put_records_response,
        get_failed_records_data.record_list,
    )
    assert failed_records_list == get_failed_records_data.expected


@mock_kinesis
def test_put_records_to_kinesis():
    stream_name = "test_stream"
    create_event_stream(stream_name)
    record_list = []
    for i in range(100):
        record_list.append(
            {
                "PartitionKey": "aa-bb",
                "Data": '{"data": {"key30": "value30", "key31": "value31"}, "datasetId": "d123", "version": "1"}',
            }
        )
    put_records_response = handler.put_records_to_kinesis(record_list, stream_name, 3)
    assert put_records_response[0]["FailedRecordCount"] == 0
    assert put_records_response[1] == []


@mock_kinesis
def test_post_events(metadata_api, mock_auth, mock_stream_name):
    stream_name = post_event_data.stream_name
    create_event_stream(stream_name)
    post_event_response = handler.post_events(post_event_data.event_with_list, {})
    assert post_event_response == post_event_data.ok_response


@mock_kinesis
def test_post_single_event(metadata_api, mock_auth, mock_stream_name):
    stream_name = post_event_data.stream_name
    create_event_stream(stream_name)
    post_event_response = handler.post_events(post_event_data.event_with_object, {})
    assert post_event_response == post_event_data.ok_response


def test_post_events_failed_records(
    metadata_api, mock_auth, failed_records, mock_stream_name
):
    post_event_response = handler.post_events(post_event_data.event_with_list, {})
    expected_response = {
        "statusCode": 500,
        "body": '{"message": "Request failed for some elements", "failedElements": [{"key00": "value00"}, {"key10": "value10"}]}',
    }
    assert post_event_response == expected_response


def test_post_events_not_found(metadata_api, mock_auth):
    post_event_response = handler.post_events(post_event_data.event_not_found, {})
    assert post_event_response == post_event_data.not_found_response


def test_post_events_metadata_server_error(metadata_api, mock_auth):
    post_event_response = handler.post_events(post_event_data.event_server_error, {})
    assert post_event_response == post_event_data.error_response


@mock_kinesis
def test_post_events_client_error(metadata_api, mock_auth, mock_stream_name):
    stream_name = "dp.green.dataset-123.incoming.version-123.json"
    create_event_stream(stream_name)
    post_event_response = handler.post_events(post_event_data.event_with_list, {})
    assert post_event_response == post_event_data.error_response


def test_post_events_decode_error(metadata_api, mock_auth):
    post_event_response = handler.post_events(post_event_data.decode_error_event, {})
    assert post_event_response == post_event_data.decode_error_response


def test_post_events_validation_error(metadata_api, mock_auth):
    post_event_response_1 = handler.post_events(
        post_event_data.validation_error_event_1, {}
    )
    post_event_response_2 = handler.post_events(
        post_event_data.validation_error_event_2, {}
    )
    assert post_event_response_1 == post_event_data.validation_error_response
    assert post_event_response_2 == post_event_data.validation_error_response


def test_post_events_forbidden(metadata_api, mock_auth):

    response = handler.post_events(post_event_data.event_access_denied, {})
    assert response == post_event_data.forbidden_response


def test_extract_event_body():
    event_body_1 = handler.extract_event_body(
        extract_event_body_test_data.event_with_list
    )
    event_body_2 = handler.extract_event_body(
        extract_event_body_test_data.event_with_object
    )

    assert event_body_1 == extract_event_body_test_data.expected_event_body
    assert event_body_2 == extract_event_body_test_data.expected_event_body


def test_post_events_webhook_auth_forbidden(metadata_api, mock_auth):
    forbidden_response = handler.events_webhook(
        post_event_data.webhook_event_access_denied, {}
    )
    assert forbidden_response["statusCode"] == 403
    assert forbidden_response["body"] == '{"message": "Forbidden"}'


def test_stream_name_identification(mock_dynamodb):
    table = create_event_streams_table()
    stream_name = handler.identify_stream_name(
        post_event_data.dataset_id,
        post_event_data.version,
        post_event_data.confidentiality,
    )
    assert stream_name == post_event_data.stream_name

    table.put_item(
        Item={
            "id": f"{post_event_data.dataset_id}/{post_event_data.version}",
            "config_version": 2,
        }
    )
    stream_name = handler.identify_stream_name(
        post_event_data.dataset_id,
        post_event_data.version,
        post_event_data.confidentiality,
    )
    assert stream_name == post_event_data.stream_name_raw


@pytest.fixture()
def metadata_api(requests_mock):
    requests_mock.register_uri(
        "GET",
        f"{handler.metadata_api_client.url}/{post_event_data.get_dataset_versions_route}",
        text=json.dumps([{"version": "1"}]),
        status_code=200,
    )

    requests_mock.register_uri(
        "GET",
        f"{handler.metadata_api_client.url}/{post_event_data.get_dataset_versions_not_exist_route}",
        text=json.dumps({"message": "Not Found"}),
        status_code=404,
    )

    requests_mock.register_uri(
        "GET",
        f"{handler.metadata_api_client.url}/datasets/{post_event_data.dataset_id}",
        text=json.dumps({"accessRights": post_event_data.access_rights}),
        status_code=200,
    )

    requests_mock.register_uri(
        "GET",
        f"{handler.metadata_api_client.url}/{post_event_data.get_dataset_versions_route_server_error}",
        text=json.dumps({"message": "Server Error"}),
        status_code=500,
    )


@pytest.fixture()
def mock_auth(monkeypatch):
    def webhook_is_authorized_response(webhook_token, dataset_id):
        if webhook_token == post_event_data.webhook_token_access_denied:
            return False, "Forbidden"
        return True

    def is_authorized_response(self, access_token, scope, resource_name):
        if (
            access_token == post_event_data.access_token
            and scope == "okdata:dataset:write"
            and resource_name.startswith("okdata:dataset:")
        ):
            return True
        return False

    monkeypatch.setattr(
        handler, "webhook_token_is_authorized", webhook_is_authorized_response
    )
    monkeypatch.setattr(ResourceAuthorizer, "has_access", is_authorized_response)


@pytest.fixture()
def failed_records(monkeypatch):
    def failed_records(record_list, stream_name, retries):
        return "", post_event_data.failed_record_list

    monkeypatch.setattr(handler, "put_records_to_kinesis", failed_records)


@pytest.fixture()
def mock_stream_name(monkeypatch):
    def identify_stream_name(dataset_id, version, confidentiality):
        return f"dp.{confidentiality}.{dataset_id}.incoming.{version}.json"

    monkeypatch.setattr(handler, "identify_stream_name", identify_stream_name)


@pytest.fixture(scope="function")
def mock_dynamodb():
    mock_dynamodb2().start()
