import json
import os
import requests

import pyntcli.log.log as log
from pyntcli.store import CredStore

PYNT_SAAS = os.environ.get("PYNT_SAAS_URL", "https://api.pynt.io/v1")

class PyntClient:
    def __init__(self, base_url=PYNT_SAAS):
        self.base_url = base_url

    def _get_headers(self):
        headers = {}
        with CredStore() as store:
            access_token = store.get_access_token()
            token_type = store.get_token_type()
            headers["Authorization"] = f"{token_type} {access_token}"
        return headers

    def get_config(self):
        url = f"{self.base_url}/config"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()  # returning actual data

        except requests.exceptions.HTTPError as e:
            raise e
        except requests.exceptions.RequestException:
            pass

        return None

    def validate_application_name_exists(self, application_name):
        url = f"{self.base_url}/application"
        headers = self._get_headers()
        query_filter = {
            "filter": json.dumps({
                "where": {
                    "name": application_name,
                },
            })
        }

        applications_response = requests.get(url, headers=headers, params=query_filter)
        if applications_response.status_code == 404:
            return False
        applications_response.raise_for_status()

        applications = applications_response.json()
        return len(applications) == 1

pynt_client = PyntClient()