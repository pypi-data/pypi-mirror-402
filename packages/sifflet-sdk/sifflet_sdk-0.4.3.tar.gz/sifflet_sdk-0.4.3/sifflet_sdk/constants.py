"""Sifflet constants"""

# Key used to access sifflet config within click context
from enum import Enum
from typing import List

# Click context
SIFFLET_CONFIG_CTX = "sifflet_config"

# Config
APP_SECTION_KEY: str = "APP"

TENANT_KEY = "TENANT"
TENANT_KEY_OS = "SIFFLET_TENANT"
BACKEND_URL_KEY = "BACKEND_URL"
BACKEND_URL_KEY_OS = "SIFFLET_BACKEND_URL"
TOKEN_KEY = "TOKEN"
TOKEN_KEY_OS = "SIFFLET_TOKEN"
DEV_MODE_KEY = "DEV_MODE"
DEBUG_KEY = "DEBUG"


# Pagination
DEFAULT_PAGE_NUM = 0
DEFAULT_PAGE_SIZE = 15

# API calls Rule run
DEFAULT_TIMEOUT_MINUTES = 5


# CLI options
class OutputType(Enum):
    TABLE = "table"
    JSON = "json"

    @classmethod
    def list(cls) -> List[str]:
        return [c.value for c in cls]


# Api enums
class StatusError(Enum):
    FAILED = "FAILED"
    TECHNICAL_ERROR = "TECHNICAL_ERROR"
    REQUIRES_YOUR_ATTENTION = "REQUIRES_YOUR_ATTENTION"

    @classmethod
    def list(cls) -> List[str]:
        return [c.value for c in cls]


class StatusSuccess(Enum):
    SUCCESS = "SUCCESS"

    @classmethod
    def list(cls) -> List[str]:
        return [c.value for c in cls]


class StatusRunning(Enum):
    RUNNING = "RUNNING"
    PENDING = "PENDING"

    @classmethod
    def list(cls) -> List[str]:
        return [c.value for c in cls]
