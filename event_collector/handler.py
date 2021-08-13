import json
import os
import uuid
from datetime import datetime
from json.decoder import JSONDecodeError

import boto3
from aws_xray_sdk.core import patch_all, xray_recorder
from boto3.dynamodb.conditions import Key
from botocore.client import ClientError
from jsonschema import validate, ValidationError
from okdata.aws.logging import logging_wrapper
from okdata.aws.logging import log_add as _log_add
from okdata.aws.logging import log_duration as _log_duration
from okdata.aws.logging import log_exception as _log_exception
from okdata.resource_auth import ResourceAuthorizer
from okdata.sdk.config import Config
from okdata.sdk.webhook.client import WebhookClient

from event_collector.handler_responses import (
    error_response,
    not_found_response,
    failed_elements_response,
    ok_response,
)
from event_collector.metadata import (
    MetadataApiClient,
    ServerErrorException,
    version_exists,
    get_confidentiality,
)


post_events_request_schema = None

metadata_api_url = os.environ["METADATA_API_URL"]
metadata_api_client = MetadataApiClient(metadata_api_url)
resource_authorizer = ResourceAuthorizer()

okdata_config = Config()
# Ensure that the sdk will not try to cache credentials on file
okdata_config.config["cacheCredentials"] = False
webhook_client = WebhookClient(okdata_config)

with open("serverless/documentation/schemas/postEventsRequest.json") as f:
    post_events_request_schema = json.loads(f.read())

patch_all()


def log_add(**kwargs):
    print(f"Adding log fields: {kwargs}")
    _log_add(**kwargs)


def log_duration(f, duration_field):
    start = datetime.now()
    print(f"Start time for {duration_field}: {start}")
    result = _log_duration(f, duration_field)
    end = datetime.now()
    print(f"End time for {duration_field}: {end}")
    return result


def log_exception(e):
    print(f"Exception: {e}")
    _log_exception(e)


@logging_wrapper
@xray_recorder.capture("post_events")
def post_events(event, context, retries=3):

    dataset_id, version = extract_path_parameters(event)
    log_add(dataset_id=dataset_id, version=version)

    try:
        dataset = metadata_api_client.get_dataset_and_versions(dataset_id)
        if not version_exists(dataset, version):
            return not_found_response(dataset_id, version)
    except ServerErrorException:
        return error_response(500, "Internal server error")

    access_token = event["headers"]["Authorization"].split(" ")[-1]
    has_access = log_duration(
        lambda: resource_authorizer.has_access(
            access_token,
            scope="okdata:dataset:write",
            resource_name=f"okdata:dataset:{dataset_id}",
        ),
        "resource_authorizer_has_access_duration",
    )
    log_add(has_access=has_access)
    if not has_access:
        return error_response(403, "Forbidden")

    event_body, validation_error_msg = validate_event_body(event)

    if validation_error_msg:
        return error_response(400, validation_error_msg)

    return send_events(dataset, version, event_body, retries)


@logging_wrapper
@xray_recorder.capture("events_webhook")
def events_webhook(event, context, retries=3):

    dataset_id, version = extract_path_parameters(event)
    webhook_token = event.get("queryStringParameters", {}).get("token")
    log_add(dataset_id=dataset_id, version=version)

    try:
        dataset = metadata_api_client.get_dataset_and_versions(dataset_id)
        if not version_exists(dataset, version):
            return not_found_response(dataset_id, version)
    except ServerErrorException:
        return error_response(500, "Internal server error")

    webhook_auth_response = log_duration(
        lambda: webhook_client.authorize_webhook_token(
            dataset_id, webhook_token, "write", retries=3
        ),
        "authorize_webhook_token_duration",
    )

    if not webhook_auth_response["access"]:
        return {
            "statusCode": 403,
            "body": json.dumps({"message": webhook_auth_response["reason"]}),
        }

    event_body, validation_error_msg = validate_event_body(event)

    if validation_error_msg:
        return error_response(400, validation_error_msg)

    return send_events(dataset, version, event_body, retries)


def send_events(dataset, version, events, retries=3):
    log_add(num_events=len(events))

    confidentiality = get_confidentiality(dataset)
    stream_name = identify_stream_name(dataset["Id"], version, confidentiality)
    log_add(confidentiality=confidentiality, stream_name=stream_name)

    try:
        record_list = event_to_record_list(events)
        kinesis_response, failed_record_list = log_duration(
            lambda: put_records_to_kinesis(record_list, stream_name, retries),
            "kinesis_put_records_duration",
        )
    except ClientError as e:
        log_exception(e)
        return error_response(500, "Internal server error")

    if len(failed_record_list) > 0:
        log_add(failed_records=len(failed_record_list))
        return failed_elements_response(failed_record_list)

    return ok_response()


def extract_event_body(event):
    body = json.loads(event["body"])
    if type(body) != list:
        return [body]
    else:
        return body


def get_event_stream(event_stream_id):
    table_name = "event-streams"
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    table = dynamodb.Table(table_name)

    event_stream_items = table.query(
        IndexName="by_id", KeyConditionExpression=Key("id").eq(event_stream_id)
    )["Items"]

    if event_stream_items:
        current_item = max(event_stream_items, key=lambda item: item["config_version"])
        return current_item

    return None


def identify_stream_name(dataset_id, version, confidentiality):
    stage = "incoming"
    event_stream = log_duration(
        lambda: get_event_stream(f"{dataset_id}/{version}"),
        "get_event_stream_duration",
    )

    if event_stream:
        stage = "raw"

    return f"dp.{confidentiality}.{dataset_id}.{stage}.{version}.json"


def put_records_to_kinesis(record_list, stream_name, retries):
    kinesis_client = boto3.client("kinesis", region_name="eu-west-1")
    put_records_response = kinesis_client.put_records(
        StreamName=stream_name, Records=record_list
    )

    # Applying retry-strategy: https://docs.aws.amazon.com/streams/latest/dev/developing-producers-with-sdk.html
    if put_records_response["FailedRecordCount"] > 0:
        failed_record_list = get_failed_records(put_records_response, record_list)
        if retries > 0:
            return put_records_to_kinesis(failed_record_list, stream_name, retries - 1)
        else:
            return put_records_response, failed_record_list
    else:
        return put_records_response, []


def get_failed_records(put_records_response, record_list):
    failed_record_list = []
    for i in range(len(record_list)):
        if "ErrorCode" in put_records_response["Records"][i]:
            failed_record_list.append(record_list[i])
    return failed_record_list


def event_to_record_list(event_body):
    record_list = []

    for element in event_body:
        record_list.append(
            {"Data": f"{json.dumps(element)}\n", "PartitionKey": str(uuid.uuid4())}
        )

    return record_list


def validate_event_body(lambda_event):
    try:
        event_body = extract_event_body(lambda_event)
        validate(event_body, post_events_request_schema)
        return event_body, None
    except JSONDecodeError as e:
        log_exception(e)
        return None, "Body is not a valid JSON document"
    except ValidationError as e:
        log_exception(e)
        return None, "JSON document does not conform to the given schema"


# https://jira.oslo.kommune.no/browse/DP-692
def extract_path_parameters(lambda_event):
    version = lambda_event["pathParameters"]["version"]

    # TODO: Replace get with default None, and remove if-condition after https://jira.oslo.kommune.no/browse/DP-692, Oyvind Nygard 25-03-2020
    dataset_id = lambda_event["pathParameters"].get("dataset_id", None)
    if not dataset_id:
        dataset_id = lambda_event["pathParameters"]["datasetId"]

    return dataset_id, version
