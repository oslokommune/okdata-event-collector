import requests
import json
import logging
from requests.exceptions import RequestException


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MetadataApiClient:
    def __init__(self, metadata_api_url):
        self.url = metadata_api_url

    def version_exists(self, dataset_id, version):
        get_version_url = f"{self.url}/datasets/{dataset_id}/versions/"
        try:

            response = requests.get(get_version_url)
        except RequestException as e:
            logger.exception(f"Error when calling metadata-api: {e}")
            raise ServerErrorException

        if response.status_code == 404:
            return False
        elif response.status_code == 500:
            raise ServerErrorException
        else:
            return contains_version(version, json.loads(response.content))


def contains_version(version, metadata_api_response):
    existing_versions = list(
        map(lambda version_item: version_item["version"], metadata_api_response)
    )
    return version in existing_versions


class ServerErrorException(Exception):
    pass
