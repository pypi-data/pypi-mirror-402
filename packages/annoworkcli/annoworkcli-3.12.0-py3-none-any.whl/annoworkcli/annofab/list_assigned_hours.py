import argparse
import logging
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas
from annoworkapi.job import get_parent_job_id_from_job_tree
from annoworkapi.resource import Resource as AnnoworkResource
from dataclasses_json import DataClassJsonMixin

import annoworkcli
import annoworkcli.common.cli
from annoworkcli.common.annofab import get_annofab_project_id_from_job
from annoworkcli.common.cli import OutputFormat, build_annoworkapi, get_list_from_args
from annoworkcli.common.utils import print_csv, print_json
from annoworkcli.schedule.list_assigned_hours_daily import ListAssignedHoursDaily

logger = logging.getLogger(__name__)


@dataclass
class AssignedHours(DataClassJsonMixin):
    """
    Annofabプロジェクトに紐づくジョブのアサイン時間情報を格納するクラス

    """

    date: str
    parent_job_id: str
    parent_job_name: str
    workspace_member_id: str
    user_id: str
    username: str
    assigned_working_hours: float


class ListAssignedHoursMain:
    def __init__(self, annowork_service: AnnoworkResource, workspace_id: str) -> None:
        self.annowork_service = annowork_service
        self.workspace_id = workspace_id
        self.list_assigned_hours_daily_obj = ListAssignedHoursDaily(annowork_service, workspace_id)

        # 全ジョブと全メンバーを取得
        self.all_jobs = self.annowork_service.api.get_jobs(self.workspace_id)
        self.all_workspace_members = self.annowork_service.api.get_workspace_members(self.workspace_id)

    def get_parent_job_id_list_from_annofab_project_id_list(self, annofab_project_id_list: list[str]) -> list[str]:
        """
        AnnofabプロジェクトIDのリストから、紐づく親ジョブIDのリストを取得します。

        Args:
            annofab_project_id_list: AnnofabプロジェクトIDのリスト

        Returns:
            親ジョブIDのリスト
        """
        annofab_project_id_set = set(annofab_project_id_list)

        def _match_job(job: dict[str, Any]) -> bool:
            af_project_id = get_annofab_project_id_from_job(job)
            if af_project_id is None:
                return False
            return af_project_id in annofab_project_id_set

        # Annofabプロジェクトに紐づくジョブを取得し、その親ジョブIDを取得
        parent_job_id_set: set[str] = set()
        for job in self.all_jobs:
            if _match_job(job):
                parent_job_id = get_parent_job_id_from_job_tree(job["job_tree"])
                if parent_job_id is not None:
                    parent_job_id_set.add(parent_job_id)

        return list(parent_job_id_set)

    def get_job_id_list_from_parent_job_id_list(self, parent_job_id_list: Collection[str]) -> list[str]:
        """
        親ジョブIDのリストから、子ジョブIDのリストを取得します。

        Args:
            parent_job_id_list: 親ジョブIDのリスト

        Returns:
            ジョブIDのリスト
        """
        parent_job_id_set = set(parent_job_id_list)
        return [e["job_id"] for e in self.all_jobs if get_parent_job_id_from_job_tree(e["job_tree"]) in parent_job_id_set]

    def list_assigned_hours(
        self,
        *,
        annofab_project_id_list: list[str],
        start_date: str | None,
        end_date: str | None,
        user_id_list: list[str] | None,
    ) -> list[AssignedHours]:
        """
        AnnofabプロジェクトIDから、紐づくジョブのアサイン時間を日ごとに取得します。

        Args:
            annofab_project_id_list: AnnofabプロジェクトIDのリスト
            start_date: 集計開始日（省略可）
            end_date: 集計終了日（省略可）
            user_id_list: 絞り込み対象のユーザIDリスト

        Returns:
            アサイン時間のリスト
        """
        # AnnofabプロジェクトIDから親ジョブIDを取得
        parent_job_id_list = self.get_parent_job_id_list_from_annofab_project_id_list(annofab_project_id_list)

        if len(parent_job_id_list) == 0:
            logger.warning(f"指定されたAnnofabプロジェクトID {annofab_project_id_list} に紐づく親ジョブが見つかりませんでした。")
            return []

        # 日次アサイン時間を取得
        assigned_hours_daily_list = self.list_assigned_hours_daily_obj.get_assigned_hours_daily_list(
            start_date=start_date,
            end_date=end_date,
            job_ids=parent_job_id_list,  # parent_job_idを指定しているのは間違っていない
            user_ids=user_id_list,
        )

        # 結果リストを作成
        result_list: list[AssignedHours] = []
        for obj in assigned_hours_daily_list:
            assert obj.job_name is not None
            assert obj.user_id is not None
            assert obj.username is not None
            result_list.append(
                AssignedHours(
                    date=obj.date,
                    parent_job_id=obj.job_id,
                    parent_job_name=obj.job_name,
                    workspace_member_id=obj.workspace_member_id,
                    user_id=obj.user_id,
                    username=obj.username,
                    assigned_working_hours=obj.assigned_working_hours,
                )
            )

        return result_list

    def main(
        self,
        *,
        output: Path,
        output_format: OutputFormat,
        annofab_project_id_list: list[str],
        start_date: str | None,
        end_date: str | None,
        user_id_list: list[str] | None,
    ) -> None:
        result = self.list_assigned_hours(
            annofab_project_id_list=annofab_project_id_list,
            start_date=start_date,
            end_date=end_date,
            user_id_list=user_id_list,
        )

        if len(result) > 0:
            result.sort(key=lambda e: (e.date, e.parent_job_id, e.workspace_member_id))
        else:
            logger.warning("アサイン時間情報は0件です。")

        logger.info(f"{len(result)} 件のアサイン時間情報を出力します。")

        if output_format == OutputFormat.JSON:
            dict_result = []
            for elm in result:
                dict_result.append(elm.to_dict())  # noqa: PERF401
            print_json(dict_result, is_pretty=True, output=output)
        else:
            if len(result) > 0:
                df = pandas.DataFrame(result)
            else:
                # 空のデータフレームを作成（属性情報を含める）
                df = pandas.DataFrame(
                    columns=[
                        "date",
                        "parent_job_id",
                        "parent_job_name",
                        "workspace_member_id",
                        "user_id",
                        "username",
                        "assigned_working_hours",
                        "annofab_account_id",
                    ]
                )
            print_csv(df, output=output)


def main(args: argparse.Namespace) -> None:
    annofab_project_id_list = get_list_from_args(args.annofab_project_id)
    user_id_list = get_list_from_args(args.user_id)
    start_date: str | None = args.start_date
    end_date: str | None = args.end_date

    if annofab_project_id_list is None:
        raise ValueError("--annofab_project_id は必須です。")

    annowork_service = build_annoworkapi(args)

    ListAssignedHoursMain(
        annowork_service=annowork_service,
        workspace_id=args.workspace_id,
    ).main(
        annofab_project_id_list=annofab_project_id_list,
        start_date=start_date,
        end_date=end_date,
        user_id_list=user_id_list,
        output=args.output,
        output_format=OutputFormat(args.format),
    )


def parse_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-w",
        "--workspace_id",
        type=str,
        required=True,
        help="対象のワークスペースID",
    )

    parser.add_argument(
        "-af_p",
        "--annofab_project_id",
        type=str,
        nargs="+",
        required=True,
        help="絞り込み対象であるAnnofabプロジェクトのproject_idを指定してください。",
    )

    parser.add_argument("-u", "--user_id", type=str, nargs="+", required=False, help="絞り込み対象のユーザID")

    parser.add_argument("--start_date", type=str, required=False, help="集計開始日(YYYY-mm-dd)")
    parser.add_argument("--end_date", type=str, required=False, help="集計終了日(YYYY-mm-dd)")

    parser.add_argument("-o", "--output", type=Path, help="出力先")

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=[e.value for e in OutputFormat],
        help="出力先のフォーマット",
        default=OutputFormat.CSV.value,
    )

    parser.set_defaults(subcommand_func=main)


def add_parser(subparsers: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    subcommand_name = "list_assigned_hours"
    subcommand_help = "Annofabプロジェクトに紐づくジョブのアサイン時間を日ごとに出力します。"

    parser = annoworkcli.common.cli.add_parser(subparsers, subcommand_name, subcommand_help, description=subcommand_help)
    parse_args(parser)
    return parser
