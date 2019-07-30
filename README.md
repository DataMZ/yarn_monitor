Yarn平台-监控项目
=================
该项目旨在监控并分析Yarn

项目简介
========
项目内容之一：监控正在运行的job日志并导出

目录
---------
项目源码:

开发项目:

  * yarn job运行时监控
  
开发工具:

  * python 3.7

项目配置:
   
  * /etc/yarnmonitor.yml需配置日志路径、yarn的Host路径、间隔时间、尝试次数等
   
 启动方式:
 ```
    方式一: python3 JobInfoController.py --application_id application_1557286909989_0005
    这里仅提供活跃的job、jobStage、jobStageDetail(仅包括RUNNING和FAILED状态)的日志信息。
    方式二: python3 JobExcelInfoController.py --application_id application_1557286909989_0005
    这里提供完成的job、jobStage、jobStageDetail信息和运行过程中出现的failed任务信息。
 ```
   
