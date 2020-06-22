import pytest
import boto3
import json
from auth import SimpleAuth
import event_collector.handler as handler
import test.test_data.event_to_record_data as event_to_record_data
import test.test_data.get_failed_records_data as get_failed_records_data
import test.test_data.post_event_data as post_event_data
import test.test_data.extract_event_body_test_data as extract_event_body_test_data
from moto import mock_kinesis


from aws_xray_sdk.core import xray_recorder

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
    put_records_response = handler.put_records_to_kinesis(record_list, stream_name, 3)
    assert put_records_response[0]["FailedRecordCount"] == 0
    assert put_records_response[1] == []


@mock_kinesis
def test_post_events(metadata_api, simple_auth):
    conn = boto3.client("kinesis", region_name="eu-west-1")
    stream_name = post_event_data.stream_name
    conn.create_stream(StreamName=stream_name, ShardCount=1)
    post_event_response = handler.post_events(post_event_data.event_with_list, {})
    assert post_event_response == post_event_data.ok_response


@mock_kinesis
def test_post_single_event(metadata_api, simple_auth):
    conn = boto3.client("kinesis", region_name="eu-west-1")
    stream_name = post_event_data.stream_name
    conn.create_stream(StreamName=stream_name, ShardCount=1)
    post_event_response = handler.post_events(post_event_data.event_with_object, {})
    assert post_event_response == post_event_data.ok_response


def test_post_events_failed_records(metadata_api, simple_auth, failed_records):
    post_event_response = handler.post_events(post_event_data.event_with_list, {})
    expected_response = {
        "statusCode": 500,
        "body": '{"message": "Request failed for some elements", "failedElements": [{"key00": "value00"}, {"key10": "value10"}]}',
    }
    assert post_event_response == expected_response


def test_post_events_not_found(metadata_api, simple_auth):
    post_event_response = handler.post_events(post_event_data.event_not_found, {})
    assert post_event_response == post_event_data.not_found_response


def test_post_events_metadata_server_error(metadata_api, simple_auth):
    post_event_response = handler.post_events(post_event_data.event_server_error, {})
    assert post_event_response == post_event_data.error_response


@mock_kinesis
def test_post_events_client_error(metadata_api, simple_auth):
    conn = boto3.client("kinesis", region_name="eu-west-1")
    stream_name = "dp.green.dataset-123.incoming.version-123.json"
    conn.create_stream(StreamName=stream_name, ShardCount=1)
    post_event_response = handler.post_events(post_event_data.event_with_list, {})
    assert post_event_response == post_event_data.error_response


def test_post_events_decode_error(metadata_api, simple_auth):
    post_event_response = handler.post_events(post_event_data.decode_error_event, {})
    assert post_event_response == post_event_data.decode_error_response


def test_post_events_validation_error(metadata_api, simple_auth):
    post_event_response_1 = handler.post_events(
        post_event_data.validation_error_event_1, {}
    )
    post_event_response_2 = handler.post_events(
        post_event_data.validation_error_event_2, {}
    )
    assert post_event_response_1 == post_event_data.validation_error_response
    assert post_event_response_2 == post_event_data.validation_error_response


def test_post_events_forbidden(metadata_api, simple_auth):

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


def test_post_events_webhook_auth_forbidden(metadata_api, simple_auth):
    forbidden_response = handler.events_webhook(
        post_event_data.webhook_event_access_denied, {}
    )
    assert forbidden_response["statusCode"] == 403
    assert forbidden_response["body"] == '{"message": "Forbidden"}'


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
        text=json.dumps({"confidentiality": post_event_data.confidentiality}),
        status_code=200,
    )

    requests_mock.register_uri(
        "GET",
        f"{handler.metadata_api_client.url}/{post_event_data.get_dataset_versions_route_server_error}",
        text=json.dumps({"message": "Server Error"}),
        status_code=500,
    )


@pytest.fixture()
def simple_auth(monkeypatch):
    def webhook_is_authorized_response(self, webhook_token, dataset_id):
        if webhook_token == post_event_data.webhook_token_access_denied:
            return False, "Forbidden"
        return True

    def is_authorized_response(self, access_token, dataset_id):
        if access_token == post_event_data.access_token_access_denied:
            return False
        return True

    monkeypatch.setattr(
        SimpleAuth, "webhook_token_is_authorized", webhook_is_authorized_response
    )
    monkeypatch.setattr(SimpleAuth, "is_authorized", is_authorized_response)


@pytest.fixture()
def failed_records(monkeypatch):
    def failed_records(record_list, stream_name, retries):
        return "", post_event_data.failed_record_list

    monkeypatch.setattr(handler, "put_records_to_kinesis", failed_records)
