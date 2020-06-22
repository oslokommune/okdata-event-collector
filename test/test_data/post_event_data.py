import json

dataset_id = "d123"
version = "1"
confidentiality = "green"
stream_name = f"dp.{confidentiality}.{dataset_id}.incoming.{version}.json"
dataset_id_not_found = "abcde"
dataset_id_server_error = "what-is-up-with-this-dataset"
access_token = "access-token"
access_token_access_denied = "access-token-denied"
webhook_token_access_denied = "webhook-token-access-denied"


get_dataset_versions_route = f"datasets/{dataset_id}/versions/{version}"
get_dataset_versions_not_exist_route = (
    f"datasets/{dataset_id_not_found}/versions/{version}"
)
get_dataset_versions_route_server_error = (
    f"datasets/{dataset_id_server_error}/versions/{version}"
)

event_with_list = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": json.dumps(
        [
            {"key00": "value00"},
            {"key10": "value10"},
            {"key20": "value20"},
            {"key30": "value30"},
        ]
    ),
    "headers": {"Authorization": f"Bearer {access_token}"},
}

event_with_object = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": json.dumps({"key00": "value00"}),
    "headers": {"Authorization": f"Bearer {access_token}"},
}

event_not_found = {
    "pathParameters": {"datasetId": dataset_id_not_found, "version": version},
    "body": json.dumps({"key00": "value00"}),
    "headers": {"Authorization": f"Bearer {access_token_access_denied}"},
}

event_access_denied = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": json.dumps({"key00": "value00"}),
    "headers": {"Authorization": f"Bearer {access_token_access_denied}"},
}

event_server_error = {
    "pathParameters": {"datasetId": dataset_id_server_error, "version": version},
    "body": json.dumps({"key00": "value00"}),
    "headers": {"Authorization": f"Bearer {access_token_access_denied}"},
}

webhook_event_access_denied = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": json.dumps({"key00": "value00"}),
    "queryStringParameters": {"token": webhook_token_access_denied},
}

ok_response = {"statusCode": 200, "body": json.dumps({"message": "Ok"})}

failed_record_list = [
    {"PartitionKey": "aa-bb", "Data": '{"key00": "value00"}'},
    {"PartitionKey": "aa-bb", "Data": '{"key10": "value10"}'},
]

not_found_response = {
    "statusCode": 404,
    "body": json.dumps(
        {
            "message": f"Dataset with id:{dataset_id_not_found} and version:{version} does not exist"
        }
    ),
}

error_response = {
    "statusCode": 500,
    "body": json.dumps({"message": "Internal server error"}),
}


decode_error_event = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": "{",
    "headers": {"Authorization": f"Bearer {access_token}"},
}

decode_error_response = {
    "statusCode": 400,
    "body": '{"message": "Body is not a valid JSON document"}',
}

validation_error_event_1 = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": '"value"',
    "headers": {"Authorization": f"Bearer {access_token}"},
}

validation_error_event_2 = {
    "pathParameters": {"datasetId": dataset_id, "version": version},
    "body": '["value"]',
    "headers": {"Authorization": f"Bearer {access_token}"},
}

validation_error_response = {
    "statusCode": 400,
    "body": '{"message": "JSON document does not conform to the given schema"}',
}

forbidden_response = {"statusCode": 403, "body": '{"message": "Forbidden"}'}
