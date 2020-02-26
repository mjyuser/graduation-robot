import re
import os


def get_number(string):
    data = re.search(r"\d+(\.\d+)?", string)
    if data is not None:
        return data.group()


def get_char(string):
    pattern = re.compile(r'[\u4e00-\u9fa5a-z0-9A-Z]+')
    result = pattern.findall(string)
    return result


def get_rootpath(item="appliance"):
    curpath = os.path.abspath(__file__)
    rootpath = curpath[:curpath.find(item) + len(item)]
    return rootpath
