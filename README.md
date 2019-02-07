Event Collector
========================

Lambda functions to put a list of records on a kinesis stream.

## Setup

1. [Install Serverless Framework](https://serverless.com/framework/docs/getting-started/)
2. Install plugins: 
```
sls plugin install -n serverless-python-requirements
sls plugin install -n serverless-aws-documentation
```

## Running tests

Tests are run using [tox](https://pypi.org/project/tox/).

```
$ tox
```

## Input event format

Example Lambda proxy HTTP event input:
```json
{
    "pathParameters": {
        "datasetId": "d123",
        "version" "v123"
    },
    "body": "[{\"key\": \"value\"}]"
}
```
