# encoding:utf-8
import logging


def logFormatInit(logFilePath):
    """
    用于初始化日志格式
    :param logFilePath: 日志文件路径
    :return: 无返回值
    """
    # 配置log的基础属性
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                        filename=logFilePath,
                        datefmt='%Y-%m-%d %H:%M:%S')
    # 设置日志打印格式
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console.setFormatter(formatter)
    # 将定义好的console日志handler添加到root logger
    logging.getLogger('').addHandler(console)

def logConsoleFormatInit():
    """
    用于初始化日志在控制台的格式
    :return: 无返回值
    """
    # 设置日志打印格式
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
