#!/usr/bin/env python3
# -*- coding: utf8 -*-

import getpass
import os
from api import PixivLoginer
from crawler import RankingCrawler

if __name__ == '__main__':
    userid = input("请输入用户名：")
    password = getpass.getpass(prompt="请输入密码：")
    saveDir = input("请输入插图保存文件夹路径：")
    if not os.path.exists(saveDir):
        os.mkdir(saveDir)
    type = '-1'
    qmNo = '-1'
    p = 1
    while int(type) < 0 or int(type) > 2:
        type = input("请选择下载类型（0:排行榜 |　1: 自选作者 ）")
        if int(type) < 0 or int(type) > 2:
            print("输入类型不对哦，请重新输入")

    if int(type) == 0:
        while int(qmNo) < 0 or int(qmNo) > 6:
            qmNo = input("请选择爬取插图排行榜类型（0：今日 | 1：本周 | 2：本月 | 3：新人 | 4：原创 |"
                     " 5：受男性欢迎 | 6：受女性欢迎 ）：")
            if int(qmNo) < 0 or int(qmNo) > 6:
                print("排行榜类型值超出范围，请重新输入")
        opener = PixivLoginer.login(userid, password)
        query_tt = RankingCrawler.download_first(opener, RankingCrawler.query_mode[int(qmNo)], saveDir)                                               # 下载第一页插图，并获取重要参数tt
        while input("当前第%d页插图已下载完成，是否继续下载第%d页插图？"
                    "（1：是 | 其他：退出）：" % (p, p + 1)) == '1':
            p += 1
            RankingCrawler.download_more(opener, RankingCrawler.uery_mode[int(qmNo)], p, RankingCrawler.query_format, query_tt, saveDir)
    elif int(type) == 1:
        print('提示：打开作者的作品页面，id=后面的那串数字就是作者的id')
        artist_id = input("请输入希望下载的作者id:")
        p_start = input('开始下载的页码数：')
        if int(p_start) > 1:
            artist_id = artist_id + '&type=all&p=' + str(p_start)
        opener = PixivLoginer.login(userid, password)
        pageCount = RankingCrawler.download_by_id(opener, artist_id, p_start, saveDir)
        p = int(p_start)
        while pageCount > p:
            p += 1
            print('准备开始下载第' + str(p) + '页')
            artist_id = artist_id + '&type=all&p=' + str(p)
            pageCount = RankingCrawler.download_by_id(opener, artist_id, p, saveDir)
    print('全部下载完啦')
    exit(0)
