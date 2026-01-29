from pathlib import Path
from typing import Any, Dict

from sifflet_sdk.apis.base import BaseApi
from sifflet_sdk.client.api import dbt_integration_api
from sifflet_sdk.errors import exception_handler
from sifflet_sdk.logger import logger


class ApiIngestion(BaseApi):
    def __init__(self, sifflet_config):
        super().__init__(sifflet_config)
        self.api_instance = dbt_integration_api.DbtIntegrationApi(self.api)

    @exception_handler
    def send_dbt_metadata(self, project_name, target, input_folder: str) -> bool:
        logger.debug(f"Sending dbt metadata to host = {self.host}")
        target_folder_path = Path(input_folder) / "target"
        manifest_file_path = target_folder_path / "manifest.json"
        catalog_file_path = target_folder_path / "catalog.json"
        run_results_file_path = target_folder_path / "run_results.json"
        artifacts: Dict[str, Any] = {}

        if manifest_file_path.is_file():
            artifacts["manifest"] = open(manifest_file_path, "rb").read()
        if catalog_file_path.is_file():
            artifacts["catalog"] = open(catalog_file_path, "rb").read()
        if run_results_file_path.is_file():
            artifacts["run_results"] = open(run_results_file_path, "rb").read()
        if not artifacts:
            raise ValueError(
                f"at least one of manifest.json, catalog.json or run_results.json must exist in {target_folder_path}"
            )

        self.api_instance.upload_dbt_metadata_files(project_name, target, **artifacts)

        return True
