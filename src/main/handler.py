import json
import boto3
import logging
import traceback
import uuid

from json.decoder import JSONDecodeError
from botocore.client import ClientError
from jsonschema import validate, ValidationError
from requests.exceptions import RequestException
from src.main.metadata_api_client import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)

post_events_request_schema = None

metadata_api_url = 'metadata.api-test.oslo.kommune.no/dev'
metadata_api_client = MetadataApiClient(metadata_api_url)

with open('serverless/documentation/schemas/postEventsRequest.json') as f:
    post_events_request_schema = json.loads(f.read())


def post_events(event, context, retries=3):
    dataset_id, version_id = event['pathParameters']['datasetId'], event['pathParameters']['version']

    try:
        metadata_api_client.get_version(dataset_id, version_id)
        event_body = extract_event_body(event)
        validate(event_body, post_events_request_schema)
        record_list = event_to_record_list(event_body)
    except JSONDecodeError as e:
        logger.exception(f'Body is not a valid JSON document: {e}')
        return error_response(400, 'Body is not a valid JSON document')
    except ValidationError as e:
        logger.exception(f'JSON document does not conform to the given schema: {e}')
        return error_response(400, 'JSON document does not conform to the given schema')
    except NotFoundException:
        return not_found_response(dataset_id, version_id)
    except ServerErrorException:
        return error_response(500, 'Internal server error')
    except RequestException as e:
        logger.exception(f'Error when calling metadata-api: {e}')
        return error_response(500, 'Internal server error')

    stream_name = f'green.{dataset_id}.incoming.{version_id}.json'

    try:
        kinesis_response, failed_record_list = put_records_to_kinesis(record_list, stream_name, retries)
    except ClientError:
        logger.error(traceback.format_exc())
        return error_response(500, 'Internal server error')

    if len(failed_record_list) > 0:
        return failed_elements_response(failed_record_list)

    return ok_response()


def extract_event_body(event):
    body = json.loads(event['body'])
    if type(body) != list:
        return [body]
    else:
        return body

def put_records_to_kinesis(record_list, stream_name, retries):
    kinesis_client = boto3.client('kinesis', region_name='eu-west-1')
    put_records_response = kinesis_client.put_records(
        StreamName=stream_name,
        Records=record_list
    )

    # Applying retry-strategy: https://docs.aws.amazon.com/streams/latest/dev/developing-producers-with-sdk.html
    if put_records_response['FailedRecordCount'] > 0:
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
        if 'ErrorCode' in put_records_response['Records'][i]:
            failed_record_list.append(record_list[i])
    return failed_record_list


def event_to_record_list(event_body):
    record_list = []

    for element in event_body:
        record_list.append(
            {
                'Data': json.dumps(element),
                'PartitionKey': str(uuid.uuid4())
            }
        )

    return record_list


def failed_elements_response(failed_record_list):
    failed_element_list = list(map(lambda record: extract_record_data(record), failed_record_list))
    lambda_proxy_response = {
        'statusCode': 500,
        'body': json.dumps({
            'message': 'Request failed for some elements',
            'failedElements': failed_element_list
        })
    }
    return lambda_proxy_response


def ok_response():
    lambda_proxy_response = {
        'statusCode': 200,
        'body': json.dumps({'message': 'Ok'})
    }
    return lambda_proxy_response

def error_response(status, message):
    return {
        'statusCode': status,
        'body': json.dumps({'message': message})
    }

def not_found_response(dataset_id, dataset_version):
    return {
        'statusCode': 404,
        'body': json.dumps({'message': f'Dataset with id:{dataset_id} and version:{dataset_version} does not exist'})
    }


def extract_record_data(record):
    return json.loads(record['Data'])
