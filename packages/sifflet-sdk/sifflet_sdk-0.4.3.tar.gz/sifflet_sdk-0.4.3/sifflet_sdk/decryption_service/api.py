from uuid import UUID

from sifflet_sdk.apis.base import BaseApi
from sifflet_sdk.client.api import rule_api, rule_run_api
from sifflet_sdk.client.models.group_decrypted_values_dto import GroupDecryptedValuesDto
from sifflet_sdk.logger import logger


class GroupDecryptionApi(BaseApi):
    def __init__(self, sifflet_config):
        super().__init__(sifflet_config)
        self.api_instance_rule = rule_api.RuleApi(self.api)
        self.api_instance_rule_run = rule_run_api.RuleRunApi(self.api)

    def fetch_rule_group_decrypted_values(self, rule_id: UUID) -> GroupDecryptedValuesDto:
        logger.debug(f"Fetch rule group decrypted values, id = {rule_id}")
        return self.api_instance_rule.decrypt_rule_groups(id=str(rule_id))

    def fetch_rule_run_group_decrypted_values(self, rule_run_id: UUID) -> GroupDecryptedValuesDto:
        logger.debug(f"Fetch rule run group decrypted values, id = {rule_run_id}")
        return self.api_instance_rule_run.decrypt_rule_run_groups(run_id=str(rule_run_id))
