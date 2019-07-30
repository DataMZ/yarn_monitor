import sys
import time
import os
sys.path.append(os.path.abspath("../.."))
import lib.util.YmlUtil as ymlUtil
import lib.util.LogUtil as logUtil
from lib.dao.JobExcelInfoGather import *
import argparse


def run(applicationID):
    yml = ymlUtil.loadYaml(os.path.abspath("../..") + "/etc/yarnmonitor.yml")
    logUtil.logConsoleFormatInit()
    job = JobExcelInfoGather(yml=yml,applicationID=applicationID)
    while True:
        job.gatherJobSummaryInfo()
        job.gatherJobStageInfo()
        job.gatherJobStageDetailInfo()
        time.sleep(float(yml.get("interval_time")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--application_id", required=True)
    args = parser.parse_args()
    applicationId = args.application_id
    run(applicationId)

