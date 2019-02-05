import json

event = {
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

ok_response = {
    'statusCode': 200,
    'body': json.dumps({'message': 'Ok'})
}

failed_record_list = [
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key00": "value00"}, "datasetId": "d123", "version": "v123"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key10": "value10"}, "datasetId": "d123", "version": "v123"}'
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
    'isBase64Encoded': False,
    'headers': {},
    'body': json.dumps({'message': f'Dataset with id:1234 and version:4321 does not exist'})
}
