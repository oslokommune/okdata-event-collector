import json

input_event = {
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

expected = [
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key00": "value00", "key01": "value01"}, "datasetId": "d123", "version": "v123"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key10": "value10", "key11": "value11"}, "datasetId": "d123", "version": "v123"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key20": "value20", "key21": "value21"}, "datasetId": "d123", "version": "v123"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key30": "value30", "key31": "value31"}, "datasetId": "d123", "version": "v123"}'
    }
]

