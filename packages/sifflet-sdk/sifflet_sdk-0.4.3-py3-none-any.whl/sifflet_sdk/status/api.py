import requests
from requests import RequestException, Response
from sifflet_sdk.apis.base import BaseApi
from sifflet_sdk.client import AccessTokenDto
from sifflet_sdk.client.api import access_token_api
from sifflet_sdk.logger import logger


class ApiStatus(BaseApi):
    def __init__(self, sifflet_config):
        super().__init__(sifflet_config)
        self.api_instance = access_token_api.AccessTokenApi(self.api)

    def fetch_health_tenant(self) -> bool:
        logger.debug(f"Check heath tenant = {self.host}")
        path: str = f"{self.host}/actuator/health"
        try:
            response: Response = requests.get(path, timeout=60)
        except RequestException:
            return False
        return response.status_code == 200

    def fetch_token_valid(self) -> AccessTokenDto:
        logger.debug(f"Check token for host = {self.host}")
        if not self.sifflet_config.token:
            raise ValueError("Token is not set")
        return self.api_instance.access_token_validity(authorization=self.sifflet_config.token)
