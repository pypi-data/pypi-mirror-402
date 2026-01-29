import time
from typing import List, Optional, Tuple

from sifflet_sdk.client.models.rule_catalog_asset_dto import RuleCatalogAssetDto
from sifflet_sdk.client.models.rule_info_dto import RuleInfoDto
from sifflet_sdk.client.models.rule_run_dto import RuleRunDto
from sifflet_sdk.constants import (
    DEFAULT_PAGE_NUM,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT_MINUTES,
    StatusError,
    StatusRunning,
    StatusSuccess,
)
from sifflet_sdk.errors import (
    SiffletRunRuleFail,
    SiffletRuntimeError,
    exception_handler,
)
from sifflet_sdk.logger import logger
from sifflet_sdk.rules.api import RulesApi


class RulesService:
    def __init__(
        self,
        sifflet_config,
        page_size=DEFAULT_PAGE_SIZE,
        page_num=DEFAULT_PAGE_NUM,
    ):
        self.api_rules = RulesApi(sifflet_config)

        self.page_size = page_size
        self.page_num = page_num

    def fetch_rules(self, filter_name) -> Tuple[List[RuleCatalogAssetDto], int]:
        rules, total_count = self.api_rules.fetch_rules(filter_name, page_size=self.page_size, page_num=self.page_num)
        return rules, total_count

    def fetch_run_history(self, rule_id) -> Tuple[RuleInfoDto, List[RuleRunDto], int]:
        rule_info: RuleInfoDto = self.api_rules.info_rule(rule_id=rule_id)

        rule_runs, total_count = self.api_rules.rule_runs(rule_id, page_size=self.page_size, page=self.page_num)

        return rule_info, rule_runs, total_count

    @exception_handler
    def run_rules(self, rule_ids: List[str]) -> List[RuleRunDto]:
        rule_runs: List[RuleRunDto] = []
        for rule_id in rule_ids:
            logger.info(f"Triggering rule {rule_id} ...")
            rule_run: RuleRunDto = self.api_rules.run_rule(rule_id)
            rule_runs.append(rule_run)
            logger.info(f"Rule {rule_id} triggered, waiting for result...")
        return rule_runs

    @exception_handler
    def wait_rule_runs(
        self,
        rule_runs: List[RuleRunDto],
        timeout: Optional[int] = 60 * DEFAULT_TIMEOUT_MINUTES,
        wait_time: int = 2,
        error_on_rule_fail: bool = True,
    ):
        start = time.monotonic()
        rule_run_fail: List[RuleRunDto] = []

        for rule_run in rule_runs:
            rule_run_result: RuleRunDto = self._wait_run(
                rule_run=rule_run, timeout=timeout, start=start, wait_time=wait_time
            )
            if rule_run_result.status in StatusSuccess.list():
                logger.info(f"Rule success, id = '{rule_run.rule_id}'")
            else:
                logger.error(
                    f"Rule failed, id = '{rule_run.id}', status = '{rule_run_result.status}',"
                    f" result = '{self._format_result_message(rule_run_result.result)}'",
                    extra={"markup": False},
                )
                rule_run_fail.append(rule_run)

        if rule_run_fail:
            details_fail = [{"id": rf.rule_id, "name": self._build_rule_name(rf.rule_id)} for rf in rule_run_fail]
            if error_on_rule_fail:
                raise SiffletRunRuleFail(f"The following rules are on fail: {details_fail}")

            logger.error(
                f"The following rules are on fail: {details_fail}. "
                f"Mark task SUCCESS as params error_on_rule_fail is False.",
                extra={"markup": False},
            )

    @staticmethod
    def _format_result_message(rule_run_result):
        return str(rule_run_result).strip().replace("\n", " ")

    def _build_rule_name(self, rule_id):
        rule_overview: RuleInfoDto = self.api_rules.info_rule(rule_id=rule_id)
        if not rule_overview.datasets:
            return rule_overview.name
        return f"[{[dataset.name for dataset in rule_overview.datasets]}]" f"{rule_overview.name}"

    @exception_handler
    def _wait_run(self, rule_run: RuleRunDto, timeout=None, start=None, wait_time=None):
        while True:
            if timeout and start + timeout < time.monotonic():
                raise SiffletRuntimeError(f"Timeout: Sifflet rule run {rule_run} not started after {timeout}s")

            time.sleep(wait_time)
            if rule_run.rule_id is None:
                raise SiffletRuntimeError(f"Rule run {rule_run} has no rule_id")
            try:
                rule_run_result: RuleRunDto = self.get_status_rule_run(
                    rule_id=rule_run.rule_id, rule_run_id=rule_run.id
                )
            except SiffletRuntimeError as err:
                logger.warning(
                    "Retrying... Sifflet API returned an error when waiting for rule run status: %s",
                    err,
                )
                continue

            run_status = rule_run_result.status
            if run_status in StatusRunning.list():
                continue
            if run_status in StatusSuccess.list() or run_status in StatusError.list():
                return rule_run_result
            raise SiffletRuntimeError(
                f"Encountered unexpected status `{rule_run_result.status}` for rule run `{rule_run}`"
            )

    def get_status_rule_run(self, rule_id: str, rule_run_id: str) -> RuleRunDto:
        rule_run_dto: RuleRunDto = self.api_rules.status_rule_run(rule_id=rule_id, run_id=rule_run_id)
        logger.debug(f"Rules status = {rule_run_dto.status}")
        return rule_run_dto
