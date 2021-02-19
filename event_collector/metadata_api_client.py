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

    def version_exists(self, dataset_id, version):
        get_version_url = f"{self.url}/datasets/{dataset_id}/versions/{version}"

        try:
            response = log_duration(
                lambda: requests.get(get_version_url),
                "metadata_get_version_duration",
            )
        except RequestException as e:
            log_exception(e)
            raise ServerErrorException

        if response.status_code == 200:
            return True

        if response.status_code == 404:
            return False
        else:
            log_add(metadata_api_response_status_code=response.status_code)
            log_add(metadata_api_response_body=response.json())
            raise ServerErrorException

    def get_confidentiality(self, dataset_id):

        get_dataset_url = f"{self.url}/datasets/{dataset_id}"
        response = log_duration(
            lambda: requests.get(get_dataset_url),
            "metadata_get_version_duration",
        )
        response.raise_for_status()

        return CONFIDENTIALITY_MAP[response.json()["accessRights"]]


class ServerErrorException(Exception):
    pass
