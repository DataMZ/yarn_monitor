#!/usr/bin/python
# -*- coding: UTF-8 -*-

# !/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 第三方 SMTP 服务
mail_host = "*"  # 设置服务器
mail_user = "*"  # 用户名
mail_pass = "*"  # 授权码

sender = '*@163.com'
receivers = ['*@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

message = MIMEText('Python 邮件发送测试...', 'plain', 'utf-8')
message['From'] = "*@163.com"
message['To'] = "*@qq.com"

subject = 'Python SMTP 邮件测试'
message['Subject'] = Header(subject, 'utf-8')

# try:
smtpObj = smtplib.SMTP()
smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
smtpObj.login(mail_user, mail_pass)
smtpObj.sendmail(sender, receivers, message.as_string())
print("邮件发送成功")
# except smtplib.SMTPException:
#     print("Error: 无法发送邮件")
smtpObj.quit()