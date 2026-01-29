from dataclasses import dataclass
from typing import Optional


@dataclass
class SiffletConfig:
    tenant: Optional[str] = None
    backend_url: Optional[str] = None
    token: Optional[str] = None
    debug: Optional[bool] = None
    application_name: Optional[str] = "sifflet-sdk"
