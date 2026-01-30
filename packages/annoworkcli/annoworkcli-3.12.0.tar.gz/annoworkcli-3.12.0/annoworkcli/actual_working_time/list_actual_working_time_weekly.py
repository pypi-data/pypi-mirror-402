import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas
from annoworkapi.job import get_parent_job_id_from_job_tree

import annoworkcli
import annoworkcli.common.cli
from annoworkcli.actual_working_time.list_actual_working_time import ListActualWorkingTime
from annoworkcli.common.cli import COMMAND_LINE_ERROR_STATUS_CODE, OutputFormat, build_annoworkapi, get_list_from_args
from annoworkcli.common.type_util import assert_noreturn
from annoworkcli.common.utils import print_csv, print_json

logger = logging.getLogger(__name__)


def get_weekly_actual_working_hours_df(actual_working_times: list[dict[str, Any]], workspace_members: list[dict[str, Any]]) -> pandas.DataFrame:
    """週単位の実績作業時間が格納されたDataFrameを生成します。

    Args:
        actual_working_times: 実績作業時間情報。start_datetime, workspace_member_id, job_id, job_name, actual_working_hours を参照します。
        workspace_members: ワークスペースメンバ情報。workspace_member_id, user_id, username を参照します。

    Returns:
        以下の列を返すDataFrame。
            "workspace_member_id", "user_id","username", "job_id", "job_name", "start_date", "end_date", "actual_working_hours"
    """
    df = pandas.DataFrame(actual_working_times)
    # 1週間ごとに集計する（日曜日始まり, 日曜日がindexになっている）
    df["dt_date"] = pandas.to_datetime(df["start_datetime"])

    df_weekly = (
        # `include_groups=False`を指定する理由：pandas2.2.0で以下の警告が出ないようにするため
        # DeprecationWarning: DataFrameGroupBy.resample operated on the grouping columns.
        # This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation.
        # Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.  # noqa: E501
        df.groupby(["workspace_member_id", "job_id"])
        .resample("W-SUN", on="dt_date", label="left", closed="left", include_groups=False)
        .agg({"actual_working_hours": "sum", "job_name": "first"})
    )
    df_weekly.reset_index(inplace=True)

    # 1週間の始まり（日曜日）と終わり（土曜日）の日付列を設定
    df_weekly.rename(columns={"dt_date": "dt_start_date"}, inplace=True)
    df_weekly["dt_end_date"] = df_weekly["dt_start_date"] + pandas.Timedelta(days=6)
    # pandas.Timestamp型をstr型に変換する
    df_weekly["start_date"] = df_weekly["dt_start_date"].dt.date.apply(lambda e: e.isoformat())
    df_weekly["end_date"] = df_weekly["dt_end_date"].dt.date.apply(lambda e: e.isoformat())

    # 実績作業時間が0の行は不要なので、除外する
    df_weekly = df_weekly.query("actual_working_hours > 0")

    df_workspace_member = pandas.DataFrame(workspace_members)

    df = df_weekly.merge(df_workspace_member, on="workspace_member_id", how="left")
    df.sort_values(["user_id", "job_id", "start_date"], inplace=True)

    return df[["workspace_member_id", "user_id", "username", "job_id", "job_name", "start_date", "end_date", "actual_working_hours"]]


def add_parent_job_info_to_df(df: pandas.DataFrame, all_jobs: list[dict[str, Any]]) -> pandas.DataFrame:
    """親ジョブ情報をDataFrameに追加します。

    Args:
        df: 実績作業時間のDataFrame。job_id列が必要です。
        all_jobs: 全ジョブのリスト。

    Returns:
        parent_job_idとparent_job_name列が追加されたDataFrame。
    """
    all_job_dict = {e["job_id"]: e for e in all_jobs}

    def get_parent_job_id(job_id: str) -> str | None:
        job = all_job_dict.get(job_id)
        if job is None:
            return None
        return get_parent_job_id_from_job_tree(job["job_tree"])

    def get_parent_job_name(parent_job_id: str | None) -> str | None:
        if parent_job_id is None:
            return None
        parent_job = all_job_dict.get(parent_job_id)
        return parent_job["job_name"] if parent_job is not None else None

    df["parent_job_id"] = df["job_id"].map(get_parent_job_id)
    df["parent_job_name"] = df["parent_job_id"].map(get_parent_job_name)

    return df


def main(args: argparse.Namespace) -> None:
    annowork_service = build_annoworkapi(args)
    job_id_list = get_list_from_args(args.job_id)
    parent_job_id_list = get_list_from_args(args.parent_job_id)
    user_id_list = get_list_from_args(args.user_id)
    start_date: str | None = args.start_date
    end_date: str | None = args.end_date

    command = " ".join(sys.argv[0:3])
    if all(v is None for v in [job_id_list, parent_job_id_list, user_id_list, start_date, end_date]):
        print(f"{command}: error: '--start_date'や'--user_id'などの絞り込み条件を1つ以上指定してください。", file=sys.stderr)  # noqa: T201
        sys.exit(COMMAND_LINE_ERROR_STATUS_CODE)

    main_obj = ListActualWorkingTime(annowork_service=annowork_service, workspace_id=args.workspace_id, timezone_offset_hours=args.timezone_offset)

    actual_working_times = main_obj.get_actual_working_times(
        job_ids=job_id_list,
        parent_job_ids=parent_job_id_list,
        start_date=start_date,
        end_date=end_date,
        user_ids=user_id_list,
        is_set_additional_info=True,
    )

    required_columns = [
        "workspace_member_id",
        "user_id",
        "username",
        "parent_job_id",
        "parent_job_name",
        "job_id",
        "job_name",
        "start_date",
        "end_date",
        "actual_working_hours",
    ]

    if len(actual_working_times) == 0:
        df = pandas.DataFrame(columns=required_columns)
    else:
        df = get_weekly_actual_working_hours_df(actual_working_times, main_obj.workspace_members)
        # 親ジョブ情報を追加
        all_jobs = annowork_service.api.get_jobs(args.workspace_id)
        df = add_parent_job_info_to_df(df, all_jobs)
        df = df[required_columns]

    logger.info(f"{len(df)} 件の週単位の実績作業時間情報を出力します。")

    match OutputFormat(args.format):
        case OutputFormat.CSV:
            print_csv(df, output=args.output)

        case OutputFormat.JSON:
            print_json(df.to_dict("records"), is_pretty=True, output=args.output)
        case _ as unreachable:
            assert_noreturn(unreachable)


def parse_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-w",
        "--workspace_id",
        type=str,
        required=True,
        help="対象のワークスペースID",
    )

    parser.add_argument("-u", "--user_id", type=str, nargs="+", required=False, help="集計対象のユーザID")

    # parent_job_idとjob_idの両方を指定するユースケースはなさそうなので、exclusiveにする。
    job_id_group = parser.add_mutually_exclusive_group()
    job_id_group.add_argument("-j", "--job_id", type=str, nargs="+", required=False, help="絞り込み対象のジョブID")
    job_id_group.add_argument("-pj", "--parent_job_id", type=str, nargs="+", required=False, help="絞り込み対象の親のジョブID")

    parser.add_argument("--start_date", type=str, required=False, help="集計開始日(YYYY-mm-dd)")
    parser.add_argument("--end_date", type=str, required=False, help="集計終了日(YYYY-mm-dd)")

    parser.add_argument(
        "--timezone_offset",
        type=float,
        help="日付に対するタイムゾーンのオフセット時間を指定します。例えばJSTなら '9' です。指定しない場合はローカルのタイムゾーンを参照します。",
    )

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
    subcommand_name = "list_weekly"
    subcommand_help = "実績作業時間の一覧を週ごと（日曜日始まり）に出力します。"

    parser = annoworkcli.common.cli.add_parser(subparsers, subcommand_name, subcommand_help, description=subcommand_help)
    parse_args(parser)
    return parser
