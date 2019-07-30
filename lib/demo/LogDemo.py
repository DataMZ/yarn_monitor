# encoding:utf-8
import logging

# 配置log的基础属性
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                    filename="D:/yarnmonitor/log/a.log",
                    datefmt='%Y-%m-%d %H:%M:%S')
# 设置日志打印格式
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s: %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
console.setFormatter(formatter)
# 将定义好的console日志handler添加到root logger
logging.getLogger('').addHandler(console)
logging.info('hello')



