import json
import boto3
import logging
import traceback

from json.decoder import JSONDecodeError
from botocore.client import ClientError
from jsonschema import validate, ValidationError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

request_schema = None

with open('serverless/documentation/schemas/postEventRequest.json') as f:
    request_schema = json.loads(f.read())


def post_event(event, context, retries=3):
    dataset_id, dataset_version = event['pathParameters']['datasetId'], event['pathParameters']['version']
    if not get_metadata(dataset_id, dataset_version):
        return not_found_response(dataset_id, dataset_version)

    try:
        validate(json.loads(event['body']), request_schema)
        record_list = event_to_record_list(event)
    except JSONDecodeError as e:
        logger.exception(f'Body is not a valid JSON document: {e}')
        return error_response(400, 'Body is not a valid JSON document')
    except ValidationError as e:
        logger.exception(f'JSON document does not conform to the given schema: {e}')
        return error_response(400, 'JSON document does not conform to the given schema')

    stream_name = f'incoming.{dataset_id}.{dataset_version}'

    try:
        kinesis_response, failed_record_list = put_records_to_kinesis(record_list, stream_name, retries)
    except ClientError:
        logger.error(traceback.format_exc())
        return error_response(500, 'Internal server error')

    if len(failed_record_list) > 0:
        return failed_elements_response(failed_record_list)

    return ok_response()


def put_records_to_kinesis(record_list, stream_name, retries):
    kinesis_client = boto3.client('kinesis', region_name='eu-west-1')
    put_records_response = kinesis_client.put_records(
        StreamName=stream_name,
        Records=record_list
    )

    # Applying retry-strategy: https://docs.aws.amazon.com/streams/latest/dev/developing-producers-with-sdk.html
    while put_records_response['FailedRecordCount'] > 0 & retries > 0:

        record_list = get_failed_records(put_records_response, record_list)

        put_records_response = kinesis_client.put_records(
            StreamName=stream_name,
            Records=record_list
        )
        retries -= 1
    return put_records_response, get_failed_records(put_records_response, record_list)


def get_failed_records(put_records_response, record_list):
    failed_record_list = []
    for i in range(len(record_list)):
        if 'ErrorCode' in put_records_response['Records'][i]:
            failed_record_list.append(record_list[i])
    return failed_record_list


def get_metadata(dataset_id, dataset_version):
    if (dataset_id, dataset_version) == ('1234', '4321'):
        return False
    return True


def event_to_record_list(event):
    record_list = []

    for element in json.loads(event['body']):
        json.loads(json.dumps(element))
        record_data = {'data': element, 'datasetId': event['pathParameters']['datasetId'],
                       'version': event['pathParameters']['version']}
        record_list.append(
            {
                'Data': json.dumps(record_data),
                'PartitionKey': 'aa-bb'
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
    return json.loads(record['Data'])['data']

