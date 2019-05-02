import json

def failed_elements_response(failed_record_list):
    failed_element_list = list(map(lambda record: json.loads(record['Data']), failed_record_list))
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
