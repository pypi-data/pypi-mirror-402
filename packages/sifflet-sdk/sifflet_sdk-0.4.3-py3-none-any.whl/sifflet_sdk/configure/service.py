import configparser
import logging
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Optional

from sifflet_sdk.config import SiffletConfig
from sifflet_sdk.constants import (
    APP_SECTION_KEY,
    BACKEND_URL_KEY,
    BACKEND_URL_KEY_OS,
    TENANT_KEY,
    TENANT_KEY_OS,
    TOKEN_KEY,
    TOKEN_KEY_OS,
)
from sifflet_sdk.logger import logger


class ConfigureService:
    path_folder_config = Path.home() / ".sifflet"
    path_file_config = path_folder_config / "config.ini"
    default_config = SiffletConfig(debug=False)

    @staticmethod
    def validate(sifflet_config: SiffletConfig) -> bool:
        if not sifflet_config.token:
            logger.error(
                f"The environment variable [italic]{TOKEN_KEY_OS}[/] must be set. "
                "You can also configure it using [bold]sifflet configure[/bold]"
            )
            return False
        if not (sifflet_config.tenant or sifflet_config.backend_url):
            logger.error(
                f"The environment variable [italic]{TENANT_KEY_OS}[/] or [italic]{BACKEND_URL_KEY_OS}[/] must be set. "
                "You can also configure it using [bold]sifflet configure[/bold]"
            )
            return False
        return True

    def configure(self, tenant: Optional[str], backend_url: Optional[str], token: Optional[str]) -> None:
        sifflet_config = SiffletConfig(
            tenant=tenant,
            backend_url=backend_url,
            token=token,
        )

        if not self.validate(sifflet_config):
            sys.exit(1)
        self.save_configuration_to_file(sifflet_config)

        logger.info(f"Sifflet configuration saved to {self.path_file_config}")

    def load_configuration(self, debug=False) -> SiffletConfig:
        """
        Initialize Sifflet configuration
        First from environment variables then falls back to configuration file
        """

        sifflet_config_from_env = self.load_configuration_from_env()
        sifflet_config_from_file = self.load_configuration_from_file()

        sifflet_config = SiffletConfig(debug=debug)
        sifflet_config = self.merge_configurations(sifflet_config, sifflet_config_from_env)
        sifflet_config = self.merge_configurations(sifflet_config, sifflet_config_from_file)
        sifflet_config = self.merge_configurations(sifflet_config, self.default_config)

        if sifflet_config.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Log level set to DEBUG")
        return sifflet_config

    def load_configuration_from_file(self) -> SiffletConfig:
        config = configparser.ConfigParser()
        config.read(self.path_file_config)

        if "APP" in config.sections():
            return SiffletConfig(
                tenant=config[APP_SECTION_KEY].get(TENANT_KEY, None),
                backend_url=config[APP_SECTION_KEY].get(BACKEND_URL_KEY, None),
                token=config[APP_SECTION_KEY].get(TOKEN_KEY, None),
            )

        return SiffletConfig()

    def save_configuration_to_file(self, sifflet_config: SiffletConfig) -> None:
        app_config = {}
        if sifflet_config.tenant is not None:
            app_config[TENANT_KEY] = sifflet_config.tenant
        if sifflet_config.backend_url is not None:
            app_config[BACKEND_URL_KEY] = sifflet_config.backend_url
        if sifflet_config.token is not None:
            app_config[TOKEN_KEY] = sifflet_config.token

        config = configparser.ConfigParser()
        config[APP_SECTION_KEY] = app_config

        self.path_folder_config.mkdir(exist_ok=True, parents=True)

        with open(self.path_file_config, mode="w", encoding="utf-8") as configfile:
            config.write(configfile)

    def load_configuration_from_env(self) -> SiffletConfig:
        config = configparser.ConfigParser()
        config.read(self.path_file_config)

        return SiffletConfig(
            tenant=os.getenv(TENANT_KEY_OS, None),
            backend_url=os.getenv(BACKEND_URL_KEY_OS, None),
            token=os.getenv(TOKEN_KEY_OS, None),
        )

    def save_configuration_to_env(self, sifflet_config: SiffletConfig) -> None:
        self.set_environment_variable(TENANT_KEY_OS, sifflet_config.tenant)
        self.set_environment_variable(BACKEND_URL_KEY_OS, sifflet_config.backend_url)
        self.set_environment_variable(TOKEN_KEY_OS, sifflet_config.token)

    @staticmethod
    def set_environment_variable(name, value):
        if value is None:
            os.unsetenv(name)
        else:
            os.putenv(name, value)

    @staticmethod
    def merge_configurations(first: SiffletConfig, second: SiffletConfig) -> SiffletConfig:
        result = deepcopy(first)
        if result.token is None:
            result.token = second.token
        if result.tenant is None:
            result.tenant = second.tenant
        if result.backend_url is None:
            result.backend_url = second.backend_url
        if result.debug is None:
            result.debug = second.debug
        return result
