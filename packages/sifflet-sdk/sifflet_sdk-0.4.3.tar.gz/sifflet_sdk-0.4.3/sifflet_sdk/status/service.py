import datetime
import json

from sifflet_sdk.client import ApiException
from sifflet_sdk.config import SiffletConfig
from sifflet_sdk.errors import exception_handler
from sifflet_sdk.logger import logger
from sifflet_sdk.status.api import ApiStatus


class StatusService:
    def __init__(self, sifflet_config):
        self.sifflet_config: SiffletConfig = sifflet_config
        self.api_rules = ApiStatus(sifflet_config)

    @exception_handler
    def check_status(self) -> bool:
        tenant_validity = self._check_tenant()

        token_validity = self._check_token() if tenant_validity else False

        return token_validity and tenant_validity

    @exception_handler
    def _check_token(self) -> bool:
        if self.sifflet_config.token is None:
            logger.warning("Token is not defined")
            return False

        token_validity: bool = False
        try:
            token = self.api_rules.fetch_token_valid()
            expiration_time = datetime.datetime.fromtimestamp(token.expiry_date / 1000.0)
            logger.info(f"Token expiration date = {expiration_time}")
            token_validity = True
        except ApiException as err:
            error_body = json.loads(err.body) if err.body else {}
            logger.error(
                f"{err.status} - {error_body['title'] if 'title' in error_body else ''} -"
                f" {error_body['detail'] if 'detail' in error_body else ''}",
                extra={"markup": False},
            )

        if token_validity:
            logger.info("Token is valid")
        else:
            logger.warning("Token is not valid")

        return token_validity

    @exception_handler
    def _check_tenant(self) -> bool:
        logger.debug(f"Tenant is set to: {self.sifflet_config.tenant}")
        tenant_validity: bool = self.api_rules.fetch_health_tenant()

        if tenant_validity:
            logger.debug(f"Connected to tenant: {self.api_rules.host}")
            logger.info("Tenant is up and reachable")
        else:
            logger.debug(f"Can't connect to tenant: {self.api_rules.host}")
            logger.warning(
                "Tenant is not reachable. " "Please check the configuration of your tenant name and your network policy"
            )

        return tenant_validity
