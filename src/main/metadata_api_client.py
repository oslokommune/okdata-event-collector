import http.client


class MetadataApiClient:
    def __init__(self, metadata_api_url):
        self.metadata_api_conn = http.client.HTTPSConnection(metadata_api_url)

    def get_version(self, dataset_id, version_id):
        response = self.metadata_api_conn.request('GET', f'/datasets/{dataset_id}/versions/{version_id}')
        return response