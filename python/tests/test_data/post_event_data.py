import json

event = {
    'pathParameters': {
        'datasetId': 'd123',
        'version': 'v123'
    },
    'body': json.dumps([
        {
            'key00': 'value00',
            'key01': 'value01'
        },
        {
            'key10': 'value10',
            'key11': 'value11'
        },
        {
            'key20': 'value20',
            'key21': 'value21'
        },
        {
            'key30': 'value30',
            'key31': 'value31'
        }
    ])
}

ok_response = {
        'statusCode': 200,
        'body': json.dumps({'message': 'Ok'})
    }