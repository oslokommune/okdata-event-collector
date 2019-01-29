import json
import boto3


def post_event(event, context, retries = 3):
    dataset_id, dataset_version = event['pathParameters']['datasetId'], event['pathParameters']['version']
    if not get_metadata(dataset_id, dataset_version):
        return not_found_response(dataset_id, dataset_version)

    record_data_list = event_to_record_data_list(event)
    stream_name=f'incoming.{dataset_id}.{dataset_version}'
    put_records_response = put_records_to_kinesis(record_data_list, stream_name)

    while put_records_response['FailedRecordCount'] > 0 & retries > 0:
        failed_record_list = []
        for i in range(record_data_list.size()):
            if 'ErrorCode' in put_records_response['Records']:
                failed_record_list.append(record_data_list[i])
        record_data_list = failed_record_list
        put_records_response = put_records_to_kinesis(record_data_list, stream_name)
        retries -= 1



def put_records_to_kinesis(record_data_list, stream_name):
    kinesis_client = boto3.client('kinesis', region_name='eu-west-1')
    response = kinesis_client.put_records(
        StreamName=stream_name,
        Records = record_data_list
    )
    return response


def get_metadata(dataset_id, dataset_version):
    if (dataset_id, dataset_version) == ('1234', '4321'):
        return True
    return False


def event_to_record_data_list(event):
    record_data_list = []

    for element in json.loads(event['body']):
        record_data = {'data': element,'datasetId': event['pathParameters']['datasetId'],'version': event['pathParameters']['version']}
        record_data_list.append(
            {
                'Data': json.dumps(record_data),
                'PartitionKey': 'aa-bb'
            }
        )

    return record_data_list

def accepted_response():
    lambda_proxy_response = {
        'statusCode': 202,
        'body': json.dumps({'message': 'Accepted'})
    }
    return lambda_proxy_response


def not_found_response(dataset_id, dataset_version):
    return {
        'statusCode': 404,
        'isBase64Encoded': False,
        'headers': {},
        'body': json.dumps({'message': f'Dataset with id:{dataset_id} and version:{dataset_version} does not exist'})
    }