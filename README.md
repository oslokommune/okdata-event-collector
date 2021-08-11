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

## Deploy

Deploy to dev is automatic via GitHub Actions, while deploy to prod can be triggered with GitHub Actions via dispatch. You can alternatively deploy from local machine (requires `saml2aws`) with: `make deploy` or `make deploy-prod`.

## Input event format

Example Lambda proxy HTTP event input:
```json
{
    "pathParameters": {
        "datasetId": "d123",
        "version": "v123"
    },
    "body": "[{\"key\": \"value\"}]"
}
```
