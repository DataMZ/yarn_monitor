# encoding:utf-8
import requests
from bs4 import BeautifulSoup
import re
import logging
import sys


class JobLogInFoGather:
    """
      JobInFoGather类,用来采集yarn平台的相关信息，内容包括正在运行job信息、stage信息以及状态为RUNNING或者FAILED的stageDetail信息
    """

    def __init__(self, hostName, applicationID, retryTime):
        """
        初始化基础信息
        :param hostName: yarn的host_name,比如http://gaaiac:8088
        :param applicationID: yarn的Job ID
        :param retryTime: 重新请求次数
        """
        self.applicationID = applicationID
        self.retryTime = retryTime
        self.currentRetryTime = 0
        self.jobHtml = '{hostName}/proxy/{applicationID}/'.format(hostName=hostName, applicationID=applicationID)
        self.activeJobIds = []
        self.activeJobStageIds = []
        self.errorJobStageDetailIds = []

    def gatherJobSummaryInfo(self):
        """
        根据现有信息抓取Job页的信息
        """
        self.activeJobIds.clear()
        try:
            jobHtmlSoup = self.getRequestSoup(self.jobHtml)
            self.gatherJobList(jobHtmlSoup)
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
                self.gatherJobStageList(jobId, jobStageHtmlSoup)
            except:
                logging.info("active stages >>> Job Id => {jobId},not gather jobStageInfo.".format(jobId=jobId))

    def gatherJobStageDetailInfo(self):
        """
        根据特定的JobId和StageId去采集Task的信息
        """
        for jobId, stageId, attempId in self.activeJobStageIds:
            try:
                jobStageDetailHtml = '{jobHtml}/stages/stage?id={stageId}&attempt={attemptId}'.format(
                    jobHtml=self.jobHtml, stageId=stageId, attemptId=attempId)  # attmpt代表尝试次数
                jobStageDetailHtmlSoup = self.getRequestSoup(jobStageDetailHtml)
                pageSoup = jobStageDetailHtmlSoup.find("div", class_="pagination")
                if pageSoup is None:  # 说明只有1页
                    self.gatherTaskList(jobId, stageId, attempId, jobStageDetailHtmlSoup)
                else:  # 说明有多页
                    pageIdList = [str(item.text).strip() for item in pageSoup.find("ul").find_all("li")][
                                 :-1]  # 删除最后一个>元素
                    self.gatherTaskList(jobId, stageId, attempId, jobStageDetailHtmlSoup)
                    for pageId in pageIdList[1:]:
                        jobStagePageDetailHtml = '{jobHtml}/stages/stage?id={stageId}&attempt={attempId}&task.page={pageId}'.format(
                            jobHtml=self.jobHtml, stageId=stageId,attempId=attempId, pageId=pageId)
                        jobStagePageDetailHtmlSoup = self.getRequestSoup(jobStagePageDetailHtml)
                        self.gatherTaskList(jobId, stageId, attempId, jobStagePageDetailHtmlSoup)
            except:
                logging.info(
                    "active stage details >>> Job Id => {jobId},  Stage Id => {stageId},  not gather taskInfo.".format(
                        jobId=jobId, stageId=stageId))

    def gatherJobList(self, soup):
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
            activeJobInfo = "active jobs >>>"
            isFailed = False
            for title, value in zip(titleList, activeJobInfoList):
                if title.find("Description") >= 0:
                    value = re.sub("\n|\(.*\)", "", value)  # Description
                if title.find("Stages") >= 0 or title.find("Tasks") >= 0:
                    value = re.sub("(\n *)", "", value)  # Stages
                if title.find("Job") >= 0:
                    self.activeJobIds.append(value)
                if title.find("Tasks") >= 0 and value.find("failed") >= 0:
                    isFailed = True
                activeJobInfo += "  {title} => {value},".format(title=title, value=value)
            if isFailed:
                logging.warning(activeJobInfo)
            else:
                logging.info(activeJobInfo)

    def gatherJobStageList(self, jobId, soup):
        """
        用于采集活动的JobStage信息
        :param jobId:  String job Id
        :param soup: Soup 传入的soup
        :return: 无返回值保存到excel当中
        """
        titleList = [str(item.text).strip() for item in
                     soup.find(id="activeStage-table").find("thead").find_all("th")]
        titleList[0] = re.sub("(\n.*)", "", titleList[0])
        activeStageTable = soup.find(id="activeStage-table").find_all("tr")
        for activeStageSoup in activeStageTable:
            activeStageInfoList = [str(item.text).strip() for item in activeStageSoup.find_all("td")]
            activeStageInfo = "active stages >>> Job Id => {jobId},".format(jobId=jobId)
            attemptId = "0"
            stageId = "0"
            isFailed = False
            for title, value in zip(titleList, activeStageInfoList):
                if title.find("Description") >= 0:
                    value = re.sub("\n.*|\(kill\)", "", value)
                if title.find("Tasks") >= 0:
                    value = re.sub("(\n *)", "", value)
                    if value.find("failed") >= 0:
                        isFailed = True
                if title.find("Stage") >= 0:
                    stageId = str(re.sub(r"\(.*\)", "", activeStageInfoList[0])).strip()  # id
                    attemptIdList = re.findall(r"\(retry (.*)\)", activeStageInfoList[0])  # attemptId
                    attemptId = "0" if len(attemptIdList) == 0 else attemptIdList[0]
                activeStageInfo += "  {title} => {value},".format(title=title, value=value)
            # taskSchedule = int(re.sub("/.*","",activeStageInfoList[4]))
            # if taskSchedule > 0:
            self.activeJobStageIds.append((jobId, stageId, attemptId))
            if isFailed:
                logging.warning(activeStageInfo)
            else:
                logging.info(activeStageInfo)

    def gatherTaskList(self, jobId, stageId, attempId, soup):
        """
        用于采集Task列表的Running和Error信息
        :param jobId:  String job Id
        :param stageId:  String stage Id
        :param attempId: String 尝试次数
        :param soup: Soup 传入的soup
        :return: 无返回值，打印在日志
        """
        titleList = [str(item.text).strip() for item in
                     soup.find(id="task-table").find("thead").find_all("th")]
        titleList[0] = re.sub("(\n.*)", "", titleList[0])
        tasksList = soup.find(id="task-table").find("tbody").find_all("tr")
        for task in tasksList:
            taskList = [str(item.text).strip() for item in task.find_all("td")]
            activeStageDetaillInfo = "active stage details >>> Job Id => {jobId},  Stage Id => {stageId},  Stage Attempt => {attempId}".format(
                jobId=jobId, stageId=stageId, attempId=attempId)
            for title, value in zip(titleList, taskList):
                if title.find("Executor") >= 0:  # clear stdout/stderr of Executor ID/Host
                    value = re.sub("\n.*", "", value)
                activeStageDetaillInfo += "  {title} => {value},".format(title=title, value=value)
            if taskList[3].find("RUNNING") >= 0:
                logging.info(activeStageDetaillInfo)
            elif taskList[3].find("FAILED") >= 0 and (jobId, stageId, attempId,tasksList[1]) not in self.errorJobStageDetailIds:
                logging.error(activeStageDetaillInfo)
                self.errorJobStageDetailIds.append((jobId, stageId, attempId,tasksList[1]))

    @staticmethod
    def getRequestSoup(url):
        """
        根据URL请求并返回soup类型
        :param url: string 正式的url
        :return: soup,请求返回的soup
        """
        htmlRequest = requests.get(url)
        htmlRequest.encoding = 'utf-8'
        return BeautifulSoup(htmlRequest.text, 'lxml')

# if __name__ == "__main__":
#     with open("D:\work_files\pycharm_codes\yarnmonitor\docs\html\jobStageHtml.html",'r',encoding="utf-8") as f:
#         jobStageDetailHtmlSoup = BeautifulSoup(f.read(), 'lxml')
#         titleList = [str(item.text).strip() for item in
#                      jobStageDetailHtmlSoup.find(id="activeStage-table").find("thead").find_all("th")]
#         print(re.sub("(\n.*)", "", titleList[0]))
#         print(titleList)
