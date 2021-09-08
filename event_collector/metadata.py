from datetime import datetime

import requests
from okdata.aws.logging import log_add as _log_add
from okdata.aws.logging import log_duration as _log_duration
from okdata.aws.logging import log_exception as _log_exception
from requests.exceptions import RequestException
from simplejson.errors import JSONDecodeError

CONFIDENTIALITY_MAP = {
    "public": "green",
    "restricted": "yellow",
    "non-public": "red",
}


def log_add(**kwargs):
    print(f"Adding log fields: {kwargs}")
    _log_add(**kwargs)


def log_duration(f, duration_field):
    start = datetime.now()
    print(f"Start time for {duration_field}: {start}")
    result = _log_duration(f, duration_field)
    end = datetime.now()
    print(f"End time for {duration_field}: {end}")
    return result


def log_exception(e):
    print(f"Exception: {e}")
    _log_exception(e)


class MetadataApiClient:
    def __init__(self, metadata_api_url):
        self.url = metadata_api_url

    def get_dataset_and_versions(self, dataset_id):
        dataset_url = f"{self.url}/datasets/{dataset_id}?embed=versions"

        try:
            response = log_duration(
                lambda: requests.get(dataset_url),
                "metadata_get_dataset_duration",
            )
        except RequestException as e:
            log_exception(e)
            raise ServerErrorException

        if response.status_code == 200:
            try:
                return response.json()
            except JSONDecodeError as e:
                # It should not happen that we get status code 200 and an empty
                # response, but it has. Handle that case gracefully by
                # pretending that it was a 404 and return None, but log an
                # exception message with the dataset ID so we can investigate
                # it further.
                log_exception(
                    "Got status code 200 but an invalid JSON response from {}: {}\n{}".format(
                        dataset_url, response.text, e
                    )
                )
                return None

        if response.status_code == 404:
            return None
        else:
            log_add(metadata_api_response_status_code=response.status_code)
            log_add(metadata_api_response_body=response.json())
            raise ServerErrorException


def version_exists(dataset, version):
    if dataset and version:
        embedded = dataset.get("_embedded", {})
        versions = [v["version"] for v in embedded.get("versions", [])]
        return version in versions
    else:
        return False


def get_confidentiality(dataset):
    return CONFIDENTIALITY_MAP[dataset["accessRights"]]


class ServerErrorException(Exception):
    pass
