import json

datasetId='d123'
versionId='v123'

get_metadata_route = f'datasets/{datasetId}/versions/{versionId}'

event_with_list = {
    'pathParameters': {
        'datasetId': datasetId,
        'version': versionId
    },
    'body': json.dumps([
        {
            'key00': 'value00'
        },
        {
            'key10': 'value10'
        },
        {
            'key20': 'value20'
        },
        {
            'key30': 'value30'
        }
    ])
}

event_with_object = {
    'pathParameters': {
        'datasetId': datasetId,
        'version': versionId
    },
    'body': json.dumps({'key00': 'value00'})
}

ok_response = {
    'statusCode': 200,
    'body': json.dumps({'message': 'Ok'})
}

failed_record_list = [
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"key00": "value00"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"key10": "value10"}'
    }
]

not_found_response = {
    'statusCode': 404,
    'body': json.dumps({'message': f'Dataset with id:{datasetId} and version:{versionId} does not exist'})
}

error_response= {
        'statusCode': 500,
        'body': json.dumps({'message': 'Internal server error'})
    }


decode_error_event = {
    'pathParameters': {
        'datasetId': datasetId,
        'version': versionId
    },
    'body': '{'
}

decode_error_response = {'statusCode': 400, 'body': '{"message": "Body is not a valid JSON document"}'}

validation_error_event_1 = {
    'pathParameters': {
        'datasetId': datasetId,
        'version': versionId
    },
    'body': '"value"'
}

validation_error_event_2 = {
    'pathParameters': {
        'datasetId': datasetId,
        'version': versionId
    },
    'body': '["value"]'
}

validation_error_response = {'statusCode': 400, 'body': '{"message": "JSON document does not conform to the given schema"}'}
