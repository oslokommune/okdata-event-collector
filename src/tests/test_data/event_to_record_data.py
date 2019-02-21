
event_body = [
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
]

expected = [
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"key00": "value00", "key01": "value01"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"key10": "value10", "key11": "value11"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"key20": "value20", "key21": "value21"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"key30": "value30", "key31": "value31"}'
    }
]
