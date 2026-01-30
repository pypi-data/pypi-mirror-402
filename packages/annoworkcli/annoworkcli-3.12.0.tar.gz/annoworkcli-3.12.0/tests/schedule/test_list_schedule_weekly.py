import os
from pathlib import Path

import pytest

from annoworkcli.schedule.list_schedule_weekly import get_weekly_assigned_hours_df

# モジュールレベルでpytestのmarkerを付ける
pytestmark = pytest.mark.access_webapi


# プロジェクトトップに移動する
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../../")

data_dir = Path("./tests/data/schedule")
out_dir = Path("./tests/out/schedule")
out_dir.mkdir(exist_ok=True, parents=True)


ASSIGNED_HOURS_DAILY_LIST = [
    {
        "workspace_member_id": "alice",
        "date": "2022-03-05",
        "assigned_working_hours": 1,
    },
    {
        "workspace_member_id": "alice",
        "date": "2022-03-06",
        "assigned_working_hours": 2,
    },
    {
        "workspace_member_id": "alice",
        "date": "2022-03-12",
        "assigned_working_hours": 3,
    },
    {
        "workspace_member_id": "bob",
        "date": "2022-02-06",
        "assigned_working_hours": 4,
    },
    {
        "workspace_member_id": "bob",
        "date": "2022-03-13",
        "assigned_working_hours": 0,
    },
]


WORKSPACE_MEMBERS = [{"workspace_member_id": "alice", "user_id": "alice", "username": "ALICE"}]


def test_get_weekly_assigned_hours_df():
    actual = get_weekly_assigned_hours_df(ASSIGNED_HOURS_DAILY_LIST, WORKSPACE_MEMBERS)
    assert len(actual) == 3
    assert actual.query("workspace_member_id == 'alice' and start_date == '2022-03-06'").iloc[0]["assigned_working_hours"] == 5
