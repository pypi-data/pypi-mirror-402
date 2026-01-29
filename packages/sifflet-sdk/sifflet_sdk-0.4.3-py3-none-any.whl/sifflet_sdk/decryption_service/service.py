import uuid
from typing import Dict, List

from sifflet_sdk.decryption_service.api import GroupDecryptionApi
from sifflet_sdk.errors import exception_handler
from sifflet_sdk.logger import logger


class GroupDecryptionService:
    def __init__(self, sifflet_config):
        self.decryption_api = GroupDecryptionApi(sifflet_config)

    @exception_handler
    def decrypt_rule_groups(self, rule_id: str) -> Dict[str, List[str]]:
        rule_uuid = uuid.UUID(rule_id)
        logger.info(f"Starting decryption for rule {rule_uuid} ...")
        decrypted_group_values = self.decryption_api.fetch_rule_group_decrypted_values(rule_uuid)
        if not decrypted_group_values or not decrypted_group_values.decrypted_values:
            raise ValueError(f"No groups found for rule {rule_uuid}.")
        logger.info(
            f"Decryption for rule {rule_id} completed. {len(decrypted_group_values.decrypted_values)} groups decrypted."
        )
        return decrypted_group_values.decrypted_values

    @exception_handler
    def decrypt_rule_run_groups(self, rule_run_id: str) -> Dict[str, List[str]]:
        rule_run_uuid = uuid.UUID(rule_run_id)
        logger.info(f"Starting decryption for rule run {rule_run_id} ...")
        decrypted_group_values = self.decryption_api.fetch_rule_run_group_decrypted_values(rule_run_uuid)
        if not decrypted_group_values or not decrypted_group_values.decrypted_values:
            raise ValueError(f"No groups found for rule run {rule_run_uuid}.")
        logger.info(
            f"Decryption for rule run {rule_run_id} completed. {len(decrypted_group_values.decrypted_values)} groups decrypted."
        )
        return decrypted_group_values.decrypted_values
