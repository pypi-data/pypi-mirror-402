import json
from datetime import datetime
from typing import List, Optional

import rich
from rich import markup
from rich.console import Console
from rich.table import Column, Table
from sifflet_cli.logger import logger
from sifflet_sdk.client.models.rule_catalog_asset_dto import RuleCatalogAssetDto
from sifflet_sdk.client.models.rule_info_dto import RuleInfoDto
from sifflet_sdk.client.models.rule_run_dto import RuleRunDto
from sifflet_sdk.constants import (
    DEFAULT_PAGE_NUM,
    OutputType,
    StatusError,
    StatusSuccess,
)
from sifflet_sdk.errors import exception_handler


class DisplayRules:
    def __init__(self, output_type: str = OutputType.TABLE.value, page_num=DEFAULT_PAGE_NUM):
        self.console = Console()
        self.output_type = OutputType(output_type)
        self.page_num = page_num

    @exception_handler
    def show_rules(self, rules, total_count, filter_name):
        """Display rules in a table"""
        if rules:
            rules_cleaned = [
                {
                    "id": rule.id,
                    "name": self._escape_markup(rule.name),
                    "datasource_type": ", ".join([dataset.datasource_type for dataset in rule.datasets]),
                    "dataset_name": ", ".join([dataset.name for dataset in rule.datasets]),
                    "platform": rule.source_platform,
                    "last_run_status": self._get_last_run_status(rule),
                    "last_run": self._get_last_run_timestamp(rule),
                }
                for rule in rules
            ]
            if self.output_type == OutputType.TABLE:
                table = Table()
                table.add_column("ID", no_wrap=True)
                table.add_column("Name", no_wrap=True)
                table.add_column("Datasource Type")
                table.add_column("Dataset")
                table.add_column("Platform")
                table.add_column("Last run status", justify="right")
                table.add_column("Last run date")
                for val in rules_cleaned:
                    table.add_row(*val.values())
                self.console.print(table)

                if len(rules) < int(total_count):
                    if self.page_num == 0:
                        self.console.print(f"Showing first {len(rules)} rules out of {total_count} rules")
                    else:
                        self.console.print(
                            f"Showing {len(rules)} rules out of {total_count} rules - page number {self.page_num}"
                        )
            else:
                self.console.print_json(json.dumps(rules_cleaned))
        elif filter_name:
            rich.print(f"No rule found for search filter: [bold]{filter_name}[/]")
        else:
            rich.print("No rule found")

    def _escape_markup(self, value: str):
        return markup.escape(value) if self.output_type == OutputType.TABLE else value

    def _format_status(self, status: str) -> str:
        if status is None:
            return ""
        result = status
        if self.output_type == OutputType.TABLE:
            if status in StatusError.__members__:
                result = f"[bold red]{status}[/bold red]"
            elif status in StatusSuccess.__members__:
                result = f"[bold green]{status}[/bold green]"

        return result

    def show_run_history(self, rule_info: RuleInfoDto, rule_runs: List[RuleRunDto], total_count: int):
        if rule_runs:
            rules_runs_cleaned = [
                {
                    "status": self._format_status(rule_run.status),
                    "start_date": str(datetime.fromtimestamp(rule_run.start_date / 1000)),
                    "end_date": str(datetime.fromtimestamp(rule_run.end_date / 1000)),
                    "type": self._escape_markup(rule_run.type),
                    "result": self._escape_markup(rule_run.result),
                }
                for rule_run in rule_runs
            ]
            table_title = f"Rule name: {rule_info.name}"
            if self.output_type == OutputType.TABLE:
                self.show_table(rules_runs_cleaned, title=table_title)
            else:
                self.console.print(rules_runs_cleaned)
            if len(rule_runs) < total_count:
                if self.page_num == 0:
                    self.console.print(f"Showing first {len(rule_runs)} runs out of {total_count} runs")
                else:
                    self.console.print(
                        f"Showing {len(rule_runs)} runs out of {total_count} runs - page number {self.page_num}"
                    )

    @staticmethod
    def _get_last_run_timestamp(rule: RuleCatalogAssetDto) -> str:
        if rule.last_run_status and rule.last_run_status.timestamp:
            return str(datetime.fromtimestamp(rule.last_run_status.timestamp / 1000))
        else:
            return ""

    def _get_last_run_status(self, rule: RuleCatalogAssetDto) -> str:
        if rule.last_run_status and rule.last_run_status.status:
            return self._format_status(rule.last_run_status.status)
        else:
            return ""

    @staticmethod
    def show_table(table: List[dict], title: Optional[str] = None) -> None:
        """Utility to display rich tables"""

        if table:
            header = list(table[0].keys())

            if "id" in header:
                header = list(filter(lambda x: x != "id", header))
                table_formatted = Table(Column(header="id", no_wrap=True), *header)
            else:
                table_formatted = Table(*header)

            for val in table:
                table_formatted.add_row(*val.values())

            table_formatted.title = title

            console = Console()
            console.print(table_formatted)
        else:
            logger.warning("No data to display")

    @staticmethod
    def show_json(data: dict) -> None:
        if data:
            console = Console()
            console.print_json(json.dumps(data))
        else:
            logger.warning("No data to display")
