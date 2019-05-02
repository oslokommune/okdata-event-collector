import requests
import json
class MetadataApiClient:
    def __init__(self, metadata_api_url):
        self.url = metadata_api_url

    def get_version(self, dataset_id, version):
        get_version_url = f'{self.url}/datasets/{dataset_id}/versions/'
        response = requests.get(get_version_url)
        if response.status_code == 404:
            raise NotFoundException
        elif response.status_code == 500:
            raise ServerErrorException
        elif response.status_code == 200 and not contains_version(version, json.loads(response.content)):
            raise NotFoundException
        else:
            return response.json()


def contains_version(version, metadata_api_response):
    existing_versions = list(map(lambda version_item: version_item['version'], metadata_api_response))
    return version in existing_versions

class NotFoundException(Exception):
    pass

class ServerErrorException(Exception):
    pass