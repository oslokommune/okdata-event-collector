import json
import boto3


def post_event(event, context, retries=3):
    dataset_id, dataset_version = event['pathParameters']['datasetId'], event['pathParameters']['version']
    if not get_metadata(dataset_id, dataset_version):
        return not_found_response(dataset_id, dataset_version)

    record_data_list = event_to_record_data_list(event)
    stream_name = f'incoming.{dataset_id}.{dataset_version}'
    kinesis_response, failed_record_list = put_records_to_kinesis(record_data_list, stream_name, retries)

    if len(failed_record_list) > 0:
        return failed_records_response(failed_record_list)

    return ok_response()


def put_records_to_kinesis(record_data_list, stream_name, retries):
    kinesis_client = boto3.client('kinesis', region_name='eu-west-1')
    put_records_response = kinesis_client.put_records(
        StreamName=stream_name,
        Records=record_data_list
    )

    # Applying retry-strategy: https://docs.aws.amazon.com/streams/latest/dev/developing-producers-with-sdk.html
    while put_records_response['FailedRecordCount'] > 0 & retries > 0:

        record_data_list = get_failed_records(put_records_response, record_data_list)

        put_records_response = kinesis_client.put_records(
            StreamName=stream_name,
            Records=record_data_list
        )
        retries -= 1
    return put_records_response, get_failed_records(put_records_response, record_data_list)


def get_failed_records(put_records_response, record_data_list):
    failed_record_list = []
    for i in range(len(record_data_list)):
        if 'ErrorCode' in put_records_response['Records'][i]:
            failed_record_list.append(record_data_list[i])
    return failed_record_list


def get_metadata(dataset_id, dataset_version):
    if (dataset_id, dataset_version) == ('1234', '4321'):
        return False
    return True


def event_to_record_data_list(event):
    record_data_list = []

    for element in json.loads(event['body']):
        record_data = {'data': element, 'datasetId': event['pathParameters']['datasetId'],
                       'version': event['pathParameters']['version']}
        record_data_list.append(
            {
                'Data': json.dumps(record_data),
                'PartitionKey': 'aa-bb'
            }
        )

    return record_data_list


def failed_records_response(failed_record_list):
    lambda_proxy_response = {
        'statusCode': 500,
        'body': json.dumps({
            'message': 'Request failed for some elements',
            'failedElements': failed_record_list
        })
    }
    return lambda_proxy_response


def ok_response():
    lambda_proxy_response = {
        'statusCode': 200,
        'body': json.dumps({'message': 'Ok'})
    }
    return lambda_proxy_response


def not_found_response(dataset_id, dataset_version):
    return {
        'statusCode': 404,
        'isBase64Encoded': False,
        'headers': {},
        'body': json.dumps({'message': f'Dataset with id:{dataset_id} and version:{dataset_version} does not exist'})
    }
