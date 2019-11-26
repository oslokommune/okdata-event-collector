import os
import uuid
import json
from json.decoder import JSONDecodeError

import boto3
from botocore.client import ClientError
from jsonschema import validate, ValidationError

from auth import SimpleAuth
from dataplatform.awslambda.logging import logging_wrapper, log_add, log_duration

from src.main.handler_responses import (
    error_response,
    not_found_response,
    failed_elements_response,
    ok_response,
)
from src.main.metadata_api_client import MetadataApiClient, ServerErrorException

post_events_request_schema = None

metadata_api_url = os.environ["METADATA_API"]
metadata_api_client = MetadataApiClient(metadata_api_url)

ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false") == "true"

with open("serverless/documentation/schemas/postEventsRequest.json") as f:
    post_events_request_schema = json.loads(f.read())


@logging_wrapper("event-collector")
def post_events(event, context, retries=3):

    dataset_id, version = (
        event["pathParameters"]["datasetId"],
        event["pathParameters"]["version"],
    )
    log_add(dataset_id=dataset_id, version=version)

    log_add(enable_auth=ENABLE_AUTH)
    if ENABLE_AUTH:
        is_owner = SimpleAuth().is_owner(event, dataset_id)
        log_add(is_owner=is_owner)
        if not is_owner:
            return error_response(403, "Forbidden")

    try:
        event_body = extract_event_body(event)
        validate(event_body, post_events_request_schema)
        record_list = event_to_record_list(event_body)
    except JSONDecodeError as e:
        log_add(exc_info=e)
        return error_response(400, "Body is not a valid JSON document")
    except ValidationError as e:
        log_add(exc_info=e)
        return error_response(400, "JSON document does not conform to the given schema")

    log_add(num_events=len(event_body))

    try:
        version_exists = log_duration(
            lambda: metadata_api_client.version_exists(dataset_id, version),
            "metadata_version_exists_duration",
        )
        log_add(version_exists=version_exists)
        if not version_exists:
            return not_found_response(dataset_id, version)
    except ServerErrorException as e:
        log_add(exc_info=e)
        return error_response(500, "Internal server error")

    confidentiality = metadata_api_client.get_confidentiality(dataset_id)
    stream_name = f"dp.{confidentiality}.{dataset_id}.incoming.{version}.json"
    log_add(confidentiality=confidentiality, stream_name=stream_name)

    try:
        kinesis_response, failed_record_list = log_duration(
            lambda: put_records_to_kinesis(record_list, stream_name, retries),
            "kinesis_put_records_duration",
        )
    except ClientError as e:
        log_add(exc_info=e)
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
