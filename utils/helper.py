import re


def get_number(string):
    data = re.search(r"\d+(\.\d+)?", string)
    if data is not None:
        return data.group()


def get_char(string):
    pattern = re.compile(r'[\u4e00-\u9fa5a-z0-9A-Z]+')
    result = pattern.findall(string)
    return result
