=========================================
schedule list_weekly
=========================================

Description
=================================
作業計画から求めたアサイン時間を週ごと（日曜日始まり）に出力します。


Examples
=================================

以下のコマンドは、2022-01-01以降のアサイン時間を出力します。

.. code-block:: 

    $ annoworkcli schedule list_weekly --workspace_id org --start_date 2022-01-01  \
     --format json --output out.json


.. code-block:: json
   :caption: out.json

   [
      {
         "workspace_member_id": "57ba0a2a-37a3-47cf-bbb6-f1087c5c5f9a",
         "user_id": "alice",
         "username": "Alice",
         "start_date": "2021-12-26",
         "end_date": "2022-01-01",
         "assigned_working_hours": 20,
      },
      {
         "workspace_member_id": "57ba0a2a-37a3-47cf-bbb6-f1087c5c5f9a",
         "user_id": "alice",
         "username": "Alice",
         "start_date": "2022-01-02",
         "end_date": "2022-01-08",
         "assigned_working_hours": 25,
      }
   ]




Usage Details
=================================

.. argparse::
   :ref: annoworkcli.schedule.list_schedule_weekly.add_parser
   :prog: annoworkcli schedule list_weekly
   :nosubcommands:
   :nodefaultconst:
