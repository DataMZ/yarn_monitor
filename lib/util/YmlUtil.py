# encoding:utf-8
import yaml

def loadYaml(yamlPath):
    """
    用于导入yaml文件
    :param yamlPath: yaml文件的路径
    :return:  返回yml的类型
    """
    f = open(yamlPath, "r")
    yml = yaml.safe_load(f)
    return yml

if __name__ == "__main__":
    import os
    yml = loadYaml(os.path.abspath("../..") + "/etc/yarnmonitor.yml")
    print(str(yml.get("completed_job_fields")) .split(","))