import sys
import time
import os
sys.path.append(os.path.abspath("../.."))
import lib.util.LogUtil as logUtil
import lib.util.YmlUtil as ymlUtil
from lib.dao.JobLogInfoGather import *
import argparse


def run(applicationID):
    yml = ymlUtil.loadYaml(os.path.abspath("../..") + "/etc/yarnmonitor.yml")
    logUtil.logFormatInit(
        "{logRootPath}/{applicationID}.log".format(logRootPath=yml.get("log_root_path"), applicationID=applicationID))
    job = JobLogInFoGather(hostName=yml.get("yarn_host_name"), applicationID=applicationID,
                           retryTime=yml.get("retry_time"))
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
