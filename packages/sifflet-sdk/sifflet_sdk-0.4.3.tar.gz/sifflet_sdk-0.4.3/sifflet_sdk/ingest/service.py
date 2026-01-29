from sifflet_sdk.config import SiffletConfig
from sifflet_sdk.errors import exception_handler
from sifflet_sdk.ingest.api import ApiIngestion


class IngestionService:
    def __init__(self, sifflet_config):
        self.sifflet_config: SiffletConfig = sifflet_config
        self.api_ingestion = ApiIngestion(sifflet_config)

    @exception_handler
    def ingest_dbt(self, project_name: str, target: str, input_folder: str) -> bool:
        return self.api_ingestion.send_dbt_metadata(project_name, target, input_folder)
