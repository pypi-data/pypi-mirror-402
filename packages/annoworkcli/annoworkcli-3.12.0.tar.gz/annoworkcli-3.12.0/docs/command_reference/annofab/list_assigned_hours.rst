=========================================
annofab list_assigned_hours
=========================================

Description
=================================
Annofabプロジェクトに紐づくジョブのアサイン時間を日ごとに出力します。



Examples
=================================

以下のコマンドは、AnnofabプロジェクトID ``af_project`` に紐づくジョブのアサイン時間を、2021-11-01から2021-11-30の期間で出力します。



.. code-block:: 

    $ annoworkcli annofab list_assigned_hours --workspace_id org \
     --annofab_project_id af_project --start_date 2021-11-01 --end_date 2021-11-30 \
     --format json --output out.json


.. code-block:: json
   :caption: out.json

   [
      {
         "date": "2021-11-05",
         "parent_job_id": "parent_job",
         "parent_job_name": "親ジョブ",
         "workspace_member_id": "58005ead-f85b-45d8-931b-54ba2837d7b1",
         "user_id": "alice",
         "username": "Alice",
         "assigned_working_hours": 1.5,
      }
   ]

.. note:: 

   ``parent_job_id`` は、``schedule list_daily`` コマンドの ``job_id`` に対応します。
   1個の親ジョブは複数のAnnofabプロジェクトに紐づく可能性があるため、出力には ``annofab_project_id`` は含まれません。


Usage Details
=================================

.. argparse::
   :ref: annoworkcli.annofab.list_assigned_hours.add_parser
   :prog: annoworkcli annofab list_assigned_hours
   :nosubcommands:
   :nodefaultconst:
