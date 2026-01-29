import urllib.request

from sifflet_sdk import client
from sifflet_sdk.config import SiffletConfig
from sifflet_sdk.errors import config_needed_handler

HEADER_APPLICATION_NAME = "X-Application-Name"


class BaseApi:
    @config_needed_handler
    def __init__(self, sifflet_config: SiffletConfig):
        self.sifflet_config = sifflet_config
        if sifflet_config.backend_url:
            self.host = sifflet_config.backend_url.rstrip("/")
        else:
            self.host = f"https://{self.sifflet_config.tenant}api.siffletdata.com"
        configuration = client.Configuration(host=self.host, access_token=self.sifflet_config.token)
        proxy_url = urllib.request.getproxies()
        if proxy_url:
            configuration.proxy = proxy_url.get("https") or proxy_url.get("http")
        self.api = client.ApiClient(
            configuration, header_name=HEADER_APPLICATION_NAME, header_value=sifflet_config.application_name
        )
