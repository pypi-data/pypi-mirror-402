import json
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sifflet_sdk.apis.base import BaseApi
from sifflet_sdk.client.api import workspace_api
from sifflet_sdk.client.exceptions import ApiException
from sifflet_sdk.client.models.as_code_workspace_dto import AsCodeWorkspaceDto
from sifflet_sdk.client.models.light_workspace_apply_request_dto import (
    LightWorkspaceApplyRequestDto,
)
from sifflet_sdk.client.models.workspace_apply_response_dto import (
    WorkspaceApplyResponseDto,
)
from sifflet_sdk.logger import logger


class ErrorAction(Enum):
    ERROR = "ERROR"
    FATAL = "FATAL"


class ObjectUntrackAction(Enum):
    DELETE = "DELETE"
    IGNORE = "IGNORE"
    ERROR = "ERROR"
    UNTRACK = "UNTRACK"


class ObjectMoveAction(Enum):
    MOVE = "MOVE"
    IGNORE = "IGNORE"
    ERROR = "ERROR"


class ObjectTrackAction(Enum):
    TRACK = "TRACK"
    IGNORE = "IGNORE"
    ERROR = "ERROR"


class WorkspaceCascadeDelete(Enum):
    ALL = "ALL"
    MONITORS = "MONITORS"
    NONE = "NONE"


class WorkspaceApi(BaseApi):
    def __init__(self, sifflet_config):
        super().__init__(sifflet_config)
        self.api_instance = workspace_api.WorkspaceApi(self.api)

    def list_workspaces(self) -> List[AsCodeWorkspaceDto]:
        response = self.api_instance.list_workspaces()
        logger.debug(f"Response: {response}")
        return response

    def delete_workspace(
        self,
        id: UUID,
        dry_run: bool,
        workspace_cascade_delete: Optional[WorkspaceCascadeDelete] = None,
    ) -> WorkspaceApplyResponseDto:
        logger.debug(f"Request: id={id}, dry_run={dry_run}, workspace_cascade_delete={workspace_cascade_delete}")
        response = self.api_instance.delete_workspace(
            str(id),
            dry_run=dry_run,
            cascade_delete=workspace_cascade_delete.value if workspace_cascade_delete else None,
        )
        # this line solves the fact that in the response, subobjects aren't converted to the correct type and are still dicts
        # this is due to _check_return_type=False, it seems needed to avoid breaking changes on the backend, didn't prioritize investigating further
        response = WorkspaceApplyResponseDto(**response.to_dict())
        logger.debug(f"Response: {response}")
        return response

    def apply_workspace(
        self,
        id: UUID,
        changes: List[Any],
        dry_run: bool,
        error_action: Optional[ErrorAction] = None,
        object_untrack_action: Optional[ObjectUntrackAction] = None,
        object_move_action: Optional[ObjectMoveAction] = None,
        object_track_action: Optional[ObjectTrackAction] = None,
    ) -> WorkspaceApplyResponseDto:
        # We do not check the type to allow the use of new monitor parameters DTO
        # Without updating the CLI
        request = LightWorkspaceApplyRequestDto(changes=changes)
        logger.debug(
            f"Request: id={id}, dry_run={dry_run}, error_action={error_action}, object_untrack_action={object_untrack_action}, object_move_action={object_move_action}, object_track_action={object_track_action}, body="
        )
        logger.debug(request)
        kwargs: Dict[str, Any] = {}
        if error_action is not None:
            kwargs["error_action"] = error_action.value
        if object_untrack_action is not None:
            kwargs["object_untrack_action"] = object_untrack_action.value
        if object_move_action is not None:
            kwargs["object_move_action"] = object_move_action.value
        if object_track_action is not None:
            kwargs["object_track_action"] = object_track_action.value
        try:
            response = self.api_instance.deploy_workspace(
                str(id),
                request,
                dry_run=dry_run,
                **kwargs,
            )

            logger.debug("Response body: %s", response)
        except ApiException as err:
            logger.debug("Error body: %s", err)
            if err.body:
                error_body = json.loads(err.body)
                if error_body.get("type") == "sifflet:errors:workspace:apply":
                    response_error = error_body["response"]
                    return WorkspaceApplyResponseDto(**response_error)
            raise err
        return response
