put_records_response = {
    'FailedRecordCount': 2,
    'Records': [
        {
            'SequenceNumber': '21269319989900637946712965403778482371',
            'ShardId': 'shardId-000000000001'
        },
        {
            'ErrorCode': "ProvisionedThroughputExceededException",
            'ErrorMessage': 'Rate exceeded for shard shardId...'
        },
        {
            'SequenceNumber': '21269319989900637946712965403778482371',
            'ShardId': 'shardId-000000000001'
        },
        {
            'ErrorCode': "ProvisionedThroughputExceededException",
            'ErrorMessage': 'Rate exceeded for shard shardId...'
        }
    ]
}

record_list = [
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

expected = [
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key10": "value10", "key11": "value11"}, "datasetId": "d123", "version": "v123"}'
    },
    {
        'PartitionKey': 'aa-bb',
        'Data': '{"data": {"key30": "value30", "key31": "value31"}, "datasetId": "d123", "version": "v123"}'
    }
]
