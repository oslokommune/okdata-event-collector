import json

event_with_list = {
    'pathParameters': {
        'datasetId': 'd123',
        'version': 'v123'
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
        'datasetId': 'd123',
        'version': 'v123'
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

event_not_found = {
    'pathParameters': {
        'datasetId': '1234',
        'version': '4321'
    },
    'body': json.dumps([
        {
            'key00': 'value00',
            'key01': 'value01'
        }
    ])
}

not_found_response = {
    'statusCode': 404,
    'body': json.dumps({'message': f'Dataset with id:1234 and version:4321 does not exist'})
}

client_error_event = {
    'pathParameters': {
        'datasetId': 'not',
        'version': 'exist'
    },
    'body': json.dumps([
        {
            'key00': 'value00'
        }
    ])
}

error_response= {
        'statusCode': 500,
        'body': json.dumps({'message': 'Internal server error'})
    }


decode_error_event = {
    'pathParameters': {
        'datasetId': 'd123',
        'version': 'v123'
    },
    'body': '{'
}

decode_error_response = {'statusCode': 400, 'body': '{"message": "Body is not a valid JSON document"}'}

validation_error_event_1 = {
    'pathParameters': {
        'datasetId': 'd123',
        'version': 'v123'
    },
    'body': '"value"'
}

validation_error_event_2 = {
    'pathParameters': {
        'datasetId': 'd123',
        'version': 'v123'
    },
    'body': '["value"]'
}

validation_error_response = {'statusCode': 400, 'body': '{"message": "JSON document does not conform to the given schema"}'}
