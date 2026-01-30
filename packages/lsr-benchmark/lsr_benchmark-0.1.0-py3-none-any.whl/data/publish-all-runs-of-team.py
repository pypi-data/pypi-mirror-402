#!/usr/bin/env python3
import click
from tira.rest_api_client import Client
from lsr_benchmark.datasets import SUPPORTED_IR_DATASETS
from lsr_benchmark.irds import TIRA_LSR_TASK_ID

@click.command()
@click.argument("team")
def main(team):
    tira = Client()
    for dataset in SUPPORTED_IR_DATASETS:
        submissions = tira.submissions(TIRA_LSR_TASK_ID, dataset)
        submissions = submissions[submissions["team"] == team]

        for _, i in submissions.iterrows():
            if i["review_blinded"] is False and i["review_published"] is True and i["review_noErrors"] is True:
                continue
            if not i["is_upload"]:
                continue
            print(i["run_id"], i["team"], i["dataset"], i["task"], i["software"])
            tira.review_run(i["run_id"], i["dataset"], i["task"], True, False, False, "")
            tira.publish_run(i["run_id"], i["dataset"], team)
            tira.unblind_run(i["run_id"], i["dataset"], team)

if __name__ == '__main__':
    main()

