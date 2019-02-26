import requests

class MetadataApiClient:
    def __init__(self, metadata_api_url):
        self.url = metadata_api_url

    def get_version(self, dataset_id, version_id):
        get_version_url = f'{self.url}/datasets/{dataset_id}/versions/{version_id}'
        response = requests.get(get_version_url)
        if response.status_code == 404:
            raise NotFoundException
        elif response.status_code == 500:
            raise ServerErrorException
        else:
            return response.json()

class NotFoundException(Exception):
    pass

class ServerErrorException(Exception):
    pass