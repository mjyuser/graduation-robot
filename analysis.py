# -*- coding:utf-8 -*-

import collections  # 词频统计

from model.mongo import mgocli
from model.robot import robot
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import platform
import wordcloud


class analysis:
    def __init__(self):
        self.mongo = robot(mgocli.instance)

    def get_data(self):
        models = self.mongo.instance.find({"labels": {"$exists": True}},
                                          {"merchant": True, "labels": True, "property": True,
                                           "feedback": True, "platform": True, "price": True})
        return models


def get_font():
    if platform.system() == "Windows":
        return FontProperties(fname="C:\Windows\Fonts\simhei.ttf")
    else:
        return FontProperties(fname="/System/Library/Fonts/PingFang.ttc")


def get_bar():
    an = analysis()
    data = an.mongo.instance.find({"labels": {"$exists": True}}, {"labels": True})
    # 获取所有的labels
    labels = []
    if data is not None:
        for x in data:
            labels.extend(str.split(x['labels'], ","))
    # labels = [x for x in labels if x]
    # 去除空值
    labels = filter(None, labels)

    labels_counts = collections.Counter(labels)
    top10 = labels_counts.most_common(10)

    k = []
    v = []
    for x in top10:
        k.append(x[0])
        v.append(x[1])
    # 绘制柱状图
    # 8 * 6 的窗口, 80像素/每英寸
    plt.figure(figsize=(8, 6), dpi=80)
    plt.subplot(1, 1, 1)
    # 柱子的总数
    N = len(k)
    index = np.arange(N)
    # 柱子的宽度
    width = 0.35
    plt.bar(index, v, width, color="#87CEFA")
    plt.xlabel("labels")
    plt.ylabel("numbers")
    plt.title("评价top10", fontproperties=get_font())
    plt.xticks(index, k, fontproperties=get_font())
    step = (v[0] - v[len(v) - 1]) / len(v)
    plt.yticks(np.arange(0, v[0] + step, step))
    plt.show()


# get_bar()


def get_wordcloud():
    an = analysis()
    data = an.mongo.instance.find({"labels": {"$exists": True}}, {"labels": True})
    labels = []
    if data is not None:
        for x in data:
            labels.extend(str.split(x['labels'], ","))
    # labels = [x for x in labels if x]
    # 去除空值
    labels = filter(None, labels)

    labels_counts = collections.Counter(labels)
    if platform.system() == "Windows":
        fp = "C:\Windows\Fonts\simhei.ttf"
    else:
        fp = "/System/Library/Fonts/PingFang.ttc"
    # 词云
    wc = wordcloud.WordCloud(
        font_path=fp,
        max_words=100,
        max_font_size=100
    )
    # 根据词频生成词云
    wc.generate_from_frequencies(labels_counts)
    plt.imshow(wc)
    # 关闭坐标轴
    plt.axis("off")
    plt.show()


# get_wordcloud()

def get_pie():
    an = analysis()
    data = an.mongo.instance.find({"merchant": {"$exists": True}}, {"merchant": True})
    merchants = [x['merchant'] for x in data if len(x['merchant']) > 0]

    merchant_count = collections.Counter(merchants)
    top10 = merchant_count.most_common(10)
    size = []
    labels = []
    explode = []
    max_merchant = top10[0][0]

    for merchant in top10:
        # percent = "{:.2f}".format(count / counts * 100)
        size.append(merchant[1])
        labels.append(merchant[0])
        if merchant[0] == max_merchant:
            explode.append(0.1)
        else:
            explode.append(0)

    # 生成饼图
    pie = plt.pie(size, labels=labels, explode=explode, autopct='%1.1f%%', shadow=True)
    # 解决饼图中文乱码的问题
    for font in pie[1]:
        font.set_fontproperties(get_font())
    plt.title("商铺商品占比", fontproperties=get_font())
    plt.axis('equal')
    plt.show()


# get_pie()
# todo 销量数据
def get_scatter():
    an = analysis()
    sales, prices = an.mongo.create_sale_data()
    plt.scatter(prices, sales)
    plt.xlabel("价格", fontproperties=get_font())
    plt.ylabel("销量", fontproperties=get_font())
    plt.title("商品价格对销量的影响", fontproperties=get_font())
    plt.show()


if __name__ == "__main__":
    # main(sys.argv[1:])
    get_scatter()
