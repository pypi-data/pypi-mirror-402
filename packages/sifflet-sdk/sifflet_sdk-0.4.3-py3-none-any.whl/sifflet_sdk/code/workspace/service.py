from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple
from uuid import UUID, uuid4

import yaml
from sifflet_sdk.client.models.as_code_workspace_dto import AsCodeWorkspaceDto
from sifflet_sdk.client.models.workspace_apply_response_dto import (
    WorkspaceApplyResponseDto,
)
from sifflet_sdk.code.workspace.api import (
    ErrorAction,
    ObjectUntrackAction,
    WorkspaceApi,
    WorkspaceCascadeDelete,
)
from sifflet_sdk.configure.service import SiffletConfig
from sifflet_sdk.errors import exception_handler
from sifflet_sdk.logger import logger


class WorkspaceService:
    def __init__(self, sifflet_config: SiffletConfig):
        self.sifflet_config: SiffletConfig = sifflet_config
        self.api_instance = WorkspaceApi(sifflet_config)

    @exception_handler
    def initialize_workspace(self, file_name: Path, name: str) -> None:
        content = yaml.dump(
            {
                "kind": "Workspace",
                "version": 1,
                "id": str(uuid4()),
                "name": name,
                "include": ["*.yaml"],
                "exclude": [],
            },
            sort_keys=False,
        )

        logger.debug("Workspace content:")
        logger.debug(content)

        with open(file_name, "w") as file:
            file.write(content)

        logger.info(f"Workspace initialized at {file_name}.")

    @exception_handler
    def initialize_monitor(self, file_name: Path, name: str) -> None:
        content = yaml.dump(
            {
                "kind": "Monitor",
                "version": 2,
                "id": str(uuid4()),
                "name": name,
                "incident": {
                    "severity": "Low",
                },
                "datasets": [{"name": "yourDatasetName"}],
                "parameters": {"kind": "MonitorKind"},
            },
            sort_keys=False,
        )

        logger.debug("Monitor content:")
        logger.debug(content)

        with open(file_name, "w") as file:
            file.write(content)

        logger.info(f"Monitor initialized at {file_name}.")

    @exception_handler
    def list_workspaces(self) -> List[AsCodeWorkspaceDto]:
        response: List[AsCodeWorkspaceDto] = self.api_instance.list_workspaces()
        return response

    @exception_handler
    def delete_workspace_by_id(self, id: UUID, dry_run: bool, cascade_delete: bool = True) -> WorkspaceApplyResponseDto:
        workspace_cascade_delete = WorkspaceCascadeDelete.ALL if cascade_delete else WorkspaceCascadeDelete.NONE
        response: WorkspaceApplyResponseDto = self.api_instance.delete_workspace(id, dry_run, workspace_cascade_delete)
        logger.info(f"{'DRY-RUN MODE - ' if dry_run else ''}Workspace deleted.")
        return response

    @exception_handler
    def delete_workspace_by_file_name(
        self, workspace_file_name: Path, dry_run: bool, cascade_delete: bool = True
    ) -> WorkspaceApplyResponseDto:
        _, workspace = self.get_workspace_content(workspace_file_name)
        return self.delete_workspace_by_id(workspace.id, dry_run, cascade_delete)

    @exception_handler
    def apply_workspace(
        self,
        workspace_file_name: Path,
        dry_run: bool,
        force_delete: bool,
        fail_on_error: bool,
    ) -> Tuple[WorkspaceApplyResponseDto, bool]:
        changes, workspace_id = self.get_changes_and_workspace_id(workspace_file_name)
        object_untrack_action = ObjectUntrackAction.DELETE if force_delete else ObjectUntrackAction.UNTRACK
        error_action = ErrorAction.FATAL if fail_on_error else ErrorAction.ERROR
        response: WorkspaceApplyResponseDto = self.api_instance.apply_workspace(
            workspace_id,
            changes,
            dry_run=dry_run,
            error_action=error_action,
            object_untrack_action=object_untrack_action,
        )

        dry_run_mode = "DRY-RUN MODE - " if dry_run else ""
        fatal_error_occurred = False
        if response is not None and response.changes is not None:
            if any(change.status == "Fatal" for change in response.changes):
                logger.error(f"{dry_run_mode}Workspace not deployed because of fatal errors.")
                fatal_error_occurred = True
            elif any(change.status == "Error" for change in response.changes):
                logger.error(f"{dry_run_mode}Workspace deployed with errors (some objects may not have been deployed).")
            elif any(log.level == "Warning" for change in response.changes for log in change.logs):  # type: ignore
                logger.warning(f"{dry_run_mode}Workspace deployed with warnings.")
            else:
                logger.info(f"{dry_run_mode}Workspace deployed.")
        else:
            logger.info(f"{dry_run_mode}Workspace deployed.")
        return response, fatal_error_occurred

    @staticmethod
    def get_changes_and_workspace_id(
        workspace_file_name: Path,
    ) -> Tuple[List[Any], UUID]:
        folder, workspace = WorkspaceService.get_workspace_content(workspace_file_name)

        # Select the files to be part of the deployment
        included_files: List[Path] = [workspace_file_name]
        for pattern in workspace.include:
            included_files.extend(folder.glob(pattern))
        excluded_files: List[Path] = []
        if workspace.exclude:
            for pattern in workspace.exclude:
                excluded_files.extend(folder.glob(pattern))
        filtered_files = {file for file in included_files if file not in excluded_files}
        logger.info(f"Included files: {[f.name for f in filtered_files]}")

        changes: List[Any] = []
        for object_file_name in filtered_files:
            with open(object_file_name, "r") as file:
                documents = yaml.safe_load_all(file)
                for file_content in documents:
                    WorkspaceService.remove_workspace_client_data(file_content)
                    changes.append(file_content)

        return changes, workspace.id

    @staticmethod
    def get_workspace_content(workspace_file_name):
        def to_workspace(data):
            if data.get("kind") != "Workspace":
                raise InvalidWorkspaceFileError("The input YAML file must be of kind Workspace")
            if data.get("version") == 1:
                return AsCodeWorkspaceV1(**data)
            raise InvalidWorkspaceFileError(f"Unsupported Workspace version: {data.get('version')}")

        # Open and parse the workspace file
        folder = workspace_file_name.parent
        with open(workspace_file_name, "r") as file:
            data = yaml.safe_load(file)
        logger.debug("Workspace content:")
        logger.debug(data)
        workspace = to_workspace(data)
        return folder, workspace

    @staticmethod
    def remove_workspace_client_data(file_content):
        if (file_content.get("kind") == "Workspace") and (file_content.get("version") == 1):
            # Remove the workspace include/exclude properties from the YAML file
            # Because they are only handled by client and are not supported by server
            if "include" in file_content:
                del file_content["include"]
            if "exclude" in file_content:
                del file_content["exclude"]


class InvalidWorkspaceFileError(Exception):
    pass


@dataclass(frozen=True)
class AsCodeWorkspaceV1:
    kind: str
    version: int
    id: UUID
    name: str
    include: List[str]
    description: Optional[str] = None
    exclude: Optional[List[str]] = None
