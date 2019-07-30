# encoding:utf-8
import requests
from bs4 import BeautifulSoup
import re
import sys
import os
import logging

sys.path.append(os.path.abspath("../.."))
import lib.util.ExcelUtil as ExcelUtil


class JobExcelInfoGather:
    """
      JobExcelInfoGather类,用来采集yarn平台的相关信息，内容包括运行完的job信息、stage信息、stage的detail信息和运行时failed的detail信息
    """

    def __init__(self, applicationID, yml):
        """
        初始化基础信息
        :param hostName: yarn的host_name,比如http://gaaiac:8088
        :param applicationID: yarn的Job ID
        :param retryTime: 重新请求次数
        """
        self.applicationID = applicationID
        self.retryTime = yml.get("retry_time")
        self.logRootPath = yml.get("log_root_path")
        self.currentRetryTime = 0
        self.jobHtml = '{hostName}/proxy/{applicationID}/'.format(hostName=yml.get("yarn_host_name"),
                                                                  applicationID=applicationID)
        self.activeJobIds = []
        self.completedJobIds = []
        self.activeJobStageIds = []
        self.completedJobStageIds = []
        self.completedJobStageIdsRecord = []
        self.errorJobStageIds = []
        self.errorJobStageDetailIds = []
        self.completedJobFields = yml.get("completed_job_fields").split(",")
        self.completedStageFields = yml.get("completed_stage_fields").split(",")
        self.completedDetailStageFields = yml.get("completed_detail_stage_fields").split(",")
        self.errorDetailStageFields = yml.get("error_detail_stage_fields").split(",")
        self.excelFile = self.initExcelInfo()

    def initExcelInfo(self):
        """
        初始化Excel对象，并用于记录信息
        :return: ExcelFile对象
        """
        excelFilePath = '{logRootPath}/{applicationID}.xlsx'.format(logRootPath=self.logRootPath,
                                                                    applicationID=self.applicationID)
        if os.path.exists(excelFilePath):
            os.remove(excelFilePath)
        excelFile = ExcelUtil.ExcelFile(excelFilePath)
        excelFile.insert(self.completedJobFields, "completed_job")
        excelFile.insert(["Job ID"] + self.completedStageFields, "completed_stage")
        excelFile.insert(["Job ID", "Stage ID", "Attemp ID"] + self.completedDetailStageFields,
                         "completed_stage_detail")
        excelFile.insert(["Job ID", "Stage ID", "Attemp ID"] + self.errorDetailStageFields, "error_stage_detail")
        excelFile.remove("Sheet")
        excelFile.save()
        return ExcelUtil.ExcelFile(excelFilePath)

    def gatherJobSummaryInfo(self):
        """
        根据现有信息抓取Job页的信息
        """
        self.activeJobIds.clear()
        try:
            jobHtmlSoup = self.getRequestSoup(self.jobHtml)
            self.gatherCompletedJobList(jobHtmlSoup)
            self.gatherActiveJobInfo(jobHtmlSoup)
        except:
            if self.currentRetryTime < self.retryTime:
                logging.info("not gather jobInfo.")
                self.currentRetryTime += 1
            else:
                logging.info("{applicationID} exit.".format(applicationID=self.applicationID))
                sys.exit(0)

    def gatherJobStageInfo(self):
        """
        根据特定的Job Stage去采集Stage的信息
        """
        self.activeJobStageIds.clear()
        for jobId in self.activeJobIds:
            try:
                jobStageHtml = '{jobHtml}/jobs/job?id={jobId}'.format(jobHtml=self.jobHtml, jobId=jobId)
                jobStageHtmlSoup = self.getRequestSoup(jobStageHtml)
                self.gatherCompletedJobStageList(jobId, jobStageHtmlSoup)
                self.gatherActiveJobStageInfo(jobId, jobStageHtmlSoup)
            except:
                logging.info("active stages >>> Job Id => {jobId},not gather jobStageInfo.".format(jobId=jobId))

    def gatherJobStageDetailInfo(self):
        """
        根据特定的JobId和StageId去采集Task的信息
        """
        for jobId, stageId, attempId in self.completedJobStageIds:
            if (jobId, stageId, attempId) not in self.completedJobStageIdsRecord:
                try:
                    jobStageDetailHtml = '{jobHtml}/stages/stage?id={stageId}&attempt={attemptId}'.format(
                        jobHtml=self.jobHtml, stageId=stageId, attemptId=attempId)  # attmpt代表尝试次数
                    jobStageDetailHtmlSoup = self.getRequestSoup(jobStageDetailHtml)
                    pageSoup = jobStageDetailHtmlSoup.find("div", class_="pagination")
                    if pageSoup is None:  # 说明只有1页
                        self.gatherTaskList(jobId, stageId, attempId, 0, jobStageDetailHtmlSoup)
                    else:  # 说明有多页
                        pageIdList = [str(item.text).strip() for item in pageSoup.find("ul").find_all("li")][
                                     :-1]  # 删除最后一个>元素
                        self.gatherTaskList(jobId, stageId, attempId, 0, jobStageDetailHtmlSoup)
                        for pageId in pageIdList[1:]:
                            jobStagePageDetailHtml = '{jobHtml}/stages/stage?id={stageId}&attempt={attempId}&task.page={pageId}'.format(
                                jobHtml=self.jobHtml, stageId=stageId, attempId=attempId, pageId=pageId)
                            jobStagePageDetailHtmlSoup = self.getRequestSoup(jobStagePageDetailHtml)
                            self.gatherTaskList(jobId, stageId, attempId, 0, jobStagePageDetailHtmlSoup)
                    self.completedJobStageIdsRecord.append((jobId, stageId, attempId))
                except:
                    logging.info(
                        "completed stage details >>> Job Id => {jobId},  Stage Id => {stageId},  not gather taskInfo.".format(
                            jobId=jobId, stageId=stageId))

        for jobId, stageId, attempId in self.activeJobStageIds:
            try:
                jobStageDetailHtml = '{jobHtml}/stages/stage?id={stageId}&attempt={attemptId}'.format(
                    jobHtml=self.jobHtml, stageId=stageId, attemptId=attempId)  # attmpt代表尝试次数
                jobStageDetailHtmlSoup = self.getRequestSoup(jobStageDetailHtml)
                pageSoup = jobStageDetailHtmlSoup.find("div", class_="pagination")
                if pageSoup is None:  # 说明只有1页
                    self.gatherTaskList(jobId, stageId, attempId, 1, jobStageDetailHtmlSoup)
                else:  # 说明有多页
                    pageIdList = [str(item.text).strip() for item in pageSoup.find("ul").find_all("li")][
                                 :-1]  # 删除最后一个>元素
                    self.gatherTaskList(jobId, stageId, attempId, 1, jobStageDetailHtmlSoup)
                    for pageId in pageIdList[1:]:
                        jobStagePageDetailHtml = '{jobHtml}/stages/stage?id={stageId}&attempt={attempId}&task.page={pageId}'.format(
                            jobHtml=self.jobHtml, stageId=stageId, attempId=attempId, pageId=pageId)
                        jobStagePageDetailHtmlSoup = self.getRequestSoup(jobStagePageDetailHtml)
                        self.gatherTaskList(jobId, stageId, attempId, 1, jobStagePageDetailHtmlSoup)
            except:
                logging.info(
                    "active stage details >>> Job Id => {jobId},  Stage Id => {stageId},  not gather taskInfo.".format(
                        jobId=jobId, stageId=stageId))

    def gatherCompletedJobList(self, soup):
        """
        :param soup: 传入的soup
        :return: 获取完整的job信息,并打印出来
        """
        try:
            titleList = [str(item.text).strip() for item in
                         soup.find(id="completedJob-table").find("thead").find_all("th")]
        except:
            titleList = []
        if len(titleList) != 0:
            titleList[0] = re.sub("(\n.*)", "", titleList[0])
            completedJobTable = soup.find(id="completedJob-table").find_all("tr")
            for completedJobSoup in completedJobTable:
                completedJobInfoSoupList = completedJobSoup.find_all("td")
                completedJobInfoList = [str(item.text).strip() for item in completedJobInfoSoupList]
                isAppend = False
                for title, value in zip(titleList, completedJobInfoList):
                    if title.find("Job") >= 0:
                        if value not in self.completedJobIds:
                            isAppend = True
                            self.completedJobIds.append(value)
                            break
                if isAppend:
                    valueList = [""] * len(self.completedJobFields)
                    for title, value in zip(titleList, completedJobInfoList):
                        if title.find("Description") >= 0:
                            value = re.sub("\n|\(.*\)", "", value)  # Description
                        if title.find("Stages") >= 0 or title.find("Tasks") >= 0:
                            value = re.sub("(\n *)", "", value)  # Stages
                        for index in range(len(self.completedJobFields)):
                            if title == self.completedJobFields[index]:
                                valueList[index] = value
                                break
                    self.excelFile.insert(valueList, "completed_job")
            self.excelFile.save()

    def gatherActiveJobInfo(self, soup):
        """
        爬取活跃Job的相关信息
        :param soup: 传入Job页面的Soup
        :return: 无返回值
        """
        titleList = [str(item.text).strip() for item in
                     soup.find(id="activeJob-table").find("thead").find_all("th")]
        titleList[0] = re.sub("\n.*", "", titleList[0])  # Job Id
        activeJobTable = soup.find(id="activeJob-table").find_all("tr")
        for activeJobSoup in activeJobTable:
            activeJobInfoSoupList = activeJobSoup.find_all("td")
            activeJobInfoList = [str(item.text).strip() for item in activeJobInfoSoupList]
            for title, value in zip(titleList, activeJobInfoList):
                if title.find("Job") >= 0:
                    self.activeJobIds.append(value)
                    break

    def gatherCompletedJobStageList(self, jobId, soup):
        """
        用于采集完成的JobStage信息
        :param jobId:  String job Id
        :param soup: Soup 传入的soup
        :return: 无返回值保存到excel当中
        """
        try:
            titleList = [str(item.text).strip() for item in
                         soup.find(id="completedStage-table").find("thead").find_all("th")]
        except:
            titleList = []
        if len(titleList) != 0:
            titleList[0] = re.sub("(\n.*)", "", titleList[0])
            completedStageTable = soup.find(id="completedStage-table").find_all("tr")
            for completedStageSoup in completedStageTable:
                completedStageInfoList = [str(item.text).strip() for item in completedStageSoup.find_all("td")]
                isAppend = False
                for title, value in zip(titleList, completedStageInfoList):
                    if title.find("Stage") >= 0:
                        stageId = str(re.sub(r"\(.*\)", "", completedStageInfoList[0])).strip()  # id
                        attemptIdList = re.findall(r"\(retry (.*)\)", completedStageInfoList[0])  # attemptId
                        attemptId = "0" if len(attemptIdList) == 0 else attemptIdList[0]
                        if (jobId, stageId, attemptId) not in self.completedJobStageIds:
                            isAppend = True
                            self.completedJobStageIds.append((jobId, stageId, attemptId))
                            break
                if isAppend:
                    valueList = [""] * len(self.completedStageFields)
                    for title, value in zip(titleList, completedStageInfoList):
                        if title.find("Description") >= 0:
                            value = re.sub("\n.*|\(kill\)", "", value)
                        if title.find("Tasks") >= 0:
                            value = re.sub("(\n *)", "", value)
                        for index in range(len(self.completedStageFields)):
                            if title == self.completedStageFields[index]:
                                valueList[index] = value
                                break
                    self.excelFile.insert([jobId] + valueList, "completed_stage")
            self.excelFile.save()

    def gatherActiveJobStageInfo(self, jobId, soup):
        titleList = [str(item.text).strip() for item in
                     soup.find(id="activeStage-table").find("thead").find_all("th")]
        titleList[0] = re.sub("(\n.*)", "", titleList[0])
        activeStageTable = soup.find(id="activeStage-table").find_all("tr")
        for activeStageSoup in activeStageTable:
            activeStageInfoList = [str(item.text).strip() for item in activeStageSoup.find_all("td")]
            for title, value in zip(titleList, activeStageInfoList):
                if title.find("Stage") >= 0:
                    stageId = str(re.sub(r"\(.*\)", "", activeStageInfoList[0])).strip()  # id
                    attemptIdList = re.findall(r"\(retry (.*)\)", activeStageInfoList[0])  # attemptId
                    attemptId = "0" if len(attemptIdList) == 0 else attemptIdList[0]
                    self.activeJobStageIds.append((jobId, stageId, attemptId))
                    break

    def gatherTaskList(self, jobId, stageId, attempId, type, soup):
        """
        用于采集完成的Task列表的Running和Error信息
        :param soup: Soup 传入的soup
        :param type: int 0 - 代表取全部字段, 1 - 代表只取error字段
        :param jobId: int jobId
        :param stageId: int stageId
        :param attempId: int attemp Id
        :return: 无返回值，打印在日志
        """
        try:
            titleList = [str(item.text).strip() for item in
                         soup.find(id="task-table").find("thead").find_all("th")]
        except:
            titleList = []
        if len(titleList) != 0:
            titleList[0] = re.sub("(\n.*)", "", titleList[0])
            tasksList = soup.find(id="task-table").find("tbody").find_all("tr")
            for task in tasksList:
                taskList = [str(item.text).strip() for item in task.find_all("td")]
                if type == 0:
                    valueList = [""] * len(self.completedDetailStageFields)
                    for title, value in zip(titleList, taskList):
                        if title.find("Executor") >= 0:  # clear stdout/stderr of Executor ID/Host
                            value = re.sub("\n.*", "", value)
                        for index in range(len(self.completedDetailStageFields)):
                            if title == self.completedDetailStageFields[index]:
                                valueList[index] = value
                                break
                    self.excelFile.insert([jobId, stageId, attempId] + valueList, "completed_stage_detail")
                elif type == 1:
                    valueList = [""] * len(self.errorDetailStageFields)
                    if taskList[3].find("FAILED") >= 0 and (jobId, stageId, attempId, tasksList[1]) not in self.errorJobStageDetailIds:
                        for title, value in zip(titleList, taskList):
                            if title.find("Executor") >= 0:  # clear stdout/stderr of Executor ID/Host
                                value = re.sub("\n.*", "", value)
                            for index in range(len(self.errorDetailStageFields)):
                                if title == self.errorDetailStageFields[index]:
                                    valueList[index] = value
                                    break
                        self.excelFile.insert([jobId, stageId, attempId] + valueList, "error_stage_detail")
                        self.errorJobStageDetailIds.append((jobId, stageId, attempId, tasksList[1]))
            self.excelFile.save()

    @staticmethod
    def getRequestSoup(url):
        """
        根据URL请求并返回soup类型
        :param url: string 正式的url
        :return: soup,请求返回的soup
        """
        htmlRequest = requests.get(url)
        htmlRequest.encoding = 'utf-8'
        logging.info("request >>> " + url)
        return BeautifulSoup(htmlRequest.text, 'lxml')


if __name__ == "__main__":
    ''
