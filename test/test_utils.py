import boto3


def create_event_stream(stream_name, region="eu-west-1"):
    conn = boto3.client("kinesis", region_name=region)
    conn.create_stream(StreamName=stream_name, ShardCount=1)
    return conn


def create_event_streams_table(item_list=[], region="eu-west-1"):
    table_name = "event-streams"
    client = boto3.client("dynamodb", region_name=region)
    client.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
            {"AttributeName": "config_version", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "config_version", "AttributeType": "N"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
        GlobalSecondaryIndexes=[
            {
                "IndexName": "by_id",
                "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 1,
                    "WriteCapacityUnits": 1,
                },
            },
        ],
    )

    table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    for item in item_list:
        table.put_item(Item=item)

    return table
