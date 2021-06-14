import requests
from okdata.aws.logging import log_add, log_exception, log_duration
from requests.exceptions import RequestException

CONFIDENTIALITY_MAP = {
    "public": "green",
    "restricted": "yellow",
    "non-public": "red",
}


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
            return response.json()

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
