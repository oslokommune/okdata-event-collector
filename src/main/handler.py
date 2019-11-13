import logging
import os
import traceback
import uuid
import json
from json.decoder import JSONDecodeError

import boto3
from botocore.client import ClientError
from jsonschema import validate, ValidationError

from auth import SimpleAuth

from src.main.handler_responses import (
    error_response,
    not_found_response,
    failed_elements_response,
    ok_response,
)
from src.main.metadata_api_client import MetadataApiClient, ServerErrorException

logger = logging.getLogger()
logger.setLevel(logging.INFO)

post_events_request_schema = None

metadata_api_url = os.environ["METADATA_API"]
metadata_api_client = MetadataApiClient(metadata_api_url)

ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false") == "true"

with open("serverless/documentation/schemas/postEventsRequest.json") as f:
    post_events_request_schema = json.loads(f.read())


def post_events(event, context, retries=3):

    dataset_id, version = (
        event["pathParameters"]["datasetId"],
        event["pathParameters"]["version"],
    )

    if ENABLE_AUTH and not SimpleAuth().is_owner(event, dataset_id):
        logger.info("Access denied")
        return error_response(403, "Forbidden")

    try:
        event_body = extract_event_body(event)
        validate(event_body, post_events_request_schema)
        record_list = event_to_record_list(event_body)
    except JSONDecodeError as e:
        logger.exception(f"Body is not a valid JSON document: {e}")
        return error_response(400, "Body is not a valid JSON document")
    except ValidationError as e:
        logger.exception(f"JSON document does not conform to the given schema: {e}")
        return error_response(400, "JSON document does not conform to the given schema")

    logger.info(f"Received {len(event_body)} events for dataset {dataset_id}/{version}")

    try:
        if not metadata_api_client.version_exists(dataset_id, version):
            return not_found_response(dataset_id, version)
    except ServerErrorException:
        logger.info("Metadata-api responded with 500 server error")
        return error_response(500, "Internal server error")

    stream_name = f"dp.green.{dataset_id}.incoming.{version}.json"

    try:
        kinesis_response, failed_record_list = put_records_to_kinesis(
            record_list, stream_name, retries
        )
    except ClientError:
        logger.error(traceback.format_exc())
        return error_response(500, "Internal server error")

    if len(failed_record_list) > 0:
        logger.warn(
            f"${len(failed_record_list)} failed records when sending to {stream_name}"
        )
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
