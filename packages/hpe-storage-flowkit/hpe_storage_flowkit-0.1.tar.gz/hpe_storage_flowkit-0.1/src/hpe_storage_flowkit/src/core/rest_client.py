import requests
from hpe_storage_flowkit.src.core import exceptions

# HTTP status code constants (extend if more needed later)
HTTP_STATUS_NOT_FOUND = 404

class RESTClient:
    def __init__(self, api_url):
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.verify_ssl = False

    def _make_url(self, endpoint):
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        return f"{self.api_url}{endpoint}"

    def get(self, endpoint, **kwargs):
        url = self._make_url(endpoint)
        response = self.session.get(url, verify=self.verify_ssl, **kwargs)
        self._check_response(response)
        return self._parse_response(response)

    def get_api_version(self, endpoint, **kwargs):
        # Extract base host URL by removing '/api' and everything after it
        if '/api' in self.api_url:
            host_url = self.api_url.split('/api')[0]
        else:
            host_url = self.api_url
            
        # Ensure endpoint starts with '/'
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
            
        url = f"{host_url}{endpoint}"
        response = self.session.get(url, verify=self.verify_ssl, **kwargs)
        self._check_response(response)
        return self._parse_response(response)
    
    def post(self, endpoint, payload=None, **kwargs):
        url = self._make_url(endpoint)
        response = self.session.post(url, json=payload, verify=self.verify_ssl, **kwargs)
        self._check_response(response)
        return self._parse_response(response)

    def put(self, endpoint, payload=None, **kwargs):
        url = self._make_url(endpoint)
        response = self.session.put(url, json=payload, verify=self.verify_ssl, **kwargs)
        self._check_response(response)
        return self._parse_response(response)

    def delete(self, endpoint, **kwargs):
        url = self._make_url(endpoint)
        response = self.session.delete(url, verify=self.verify_ssl, **kwargs)
        self._check_response(response)
        return self._parse_response(response)

    def _check_response(self, response):
        if response.status_code == HTTP_STATUS_NOT_FOUND:
            raise exceptions.HTTPNotFound("Resource not found")
        elif not response.ok:
            raise exceptions.HPEStorageException(f"HTTP {response.status_code}: {response.text}")

    def _parse_response(self, response):
        if response.text:
            try:
                return response.json()
            except Exception:
                return response.text
        return None
