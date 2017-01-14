#!/usr/bin/env python3
# -*- coding: utf8 -*-

import urllib.request
import urllib.parse
import os.path
import utils
import time
import json
import getpass
from bs4 import BeautifulSoup
from api import PixivLoginer
from crawler import PixivItem
pixiv_url = 'http://www.pixiv.net'
pixiv_url_ranking = 'http://www.pixiv.net/ranking.php'
pixiv_url_artist = 'http://www.pixiv.net/member_illust.php?id='
artist_id = ''
isRank = True
query_mode = (
    'daily',
    'weekly',
    'monthly',
    'rookie',
    'original',
    'male',
    'female'
)
pageCount = 1
query_format = 'json'

def analysis_html(html, isRank):

    items = []
    rootSoup = BeautifulSoup(html, 'lxml')
    last_page = 0
    if isRank:

        selector = rootSoup.select('#wrapper > div.layout-body > div > '
                               'div.ranking-items-container > div.ranking-items.adjust > section')
        for child in selector:
            linkUrl = child.select('div.ranking-image-item > a')[0]['href']
            illust_id = child['data-id']
            thumbnailUrl = child.select('div.ranking-image-item > a > div > img')[0]['data-src']

            author = child['data-user-name']
            browse = child['data-view-count']
            score = child['data-total-score']
            date = child['data-date']
            title = child['data-title']

            originalUrl1 = thumbnailUrl.replace('c/240x480/img-master', 'img-original')
            originalUrl2 = thumbnailUrl.replace('c/240x480/img-master', 'c/1200x1200/img-master')

            items.append(PixivItem(title, illust_id, author, date, browse, score, linkUrl,
                                   thumbnailUrl, originalUrl1, originalUrl2))

    if not isRank:
        selector = rootSoup.select('#wrapper > div.layout-a > div.layout-column-2 > '
                               'div._unit.manage-unit > div > ul._image-items > li.image-item')
        author = rootSoup.select('h1.user')[0].text
        browse = 'unknow'
        score = 'unknow'
        date = 'unknow'
        title = 'title'
        len = rootSoup.select('ul.page-list')[0].select('li').__len__() #获取页码总数
        if rootSoup.select('ul.page-list')[0].select('li')[len - 1].select('a').__len__() == 0:
            last_page = int(rootSoup.select('ul.page-list')[0].select('li')[len - 1].text)
        else:
            last_page = int(rootSoup.select('ul.page-list')[0].select('li')[len - 1].select('a')[0].text)
        for child in selector:
            linkUrl = child.select('a.work._work')[0]['href']
            illust_id = child.select('a.work._work > div._layout-thumbnail > img')[0]['data-id']
            thumbnailUrl = child.select('a.work._work > div._layout-thumbnail > img')[0]['data-src']
            originalUrl1 = thumbnailUrl.replace('c/150x150/img-master', 'img-original')
            originalUrl2 = thumbnailUrl.replace('c/150x150/img-master', 'c/1200x1200/img-master')

            items.append(PixivItem(title, illust_id, author, date, browse, score, linkUrl,
                                   thumbnailUrl, originalUrl1, originalUrl2))
    return (items, last_page)

def analysis_multiple(html, op):                                                                                        #下载多图
    items = []
    rootSoup = BeautifulSoup(html, 'lxml')
    selector = rootSoup.select('#wrapper > div.layout-a > div.layout-column-2 > '
                           'div._unit.manage-unit > div > ul._image-items > li.image-item > a.work._work.multiple')

    author = rootSoup.select('h1.user')[0].text
    browse = 'unknow'
    score = 'unknow'
    date = 'unknow'
    title = 'title'
    for child in selector:
        illust_id = child.select('div._layout-thumbnail > img')[0]['data-id'] + '_'
        multi_url = pixiv_url + child['href'].replace('medium', 'manga')
        with op.open(multi_url) as f:
            if f.status == 200:
                multiHtml = utils.ungzip(f.read()).decode()
                multiSoup = BeautifulSoup(multiHtml, 'lxml')
                multiSelector = multiSoup.select('#main > section.manga > div.item-container')
                for multiChild in multiSelector:
                    index = multiChild.select('img')[0]['data-index']
                    illust_id_this = illust_id + str(index)
                    linkUrl = multiChild.select('a')[0]['href']
                    thumbnailUrl = multiChild.select('img')[0]['data-src']
                    originalUrl1 = thumbnailUrl.replace('c/1200x1200/img-master', 'img-original').replace('_master1200', '')
                    originalUrl2 = thumbnailUrl.replace('c/1200x1200/img-master', 'c/1200x1200/img-master')
                    items.append(PixivItem(title, illust_id_this, author, date, browse, score, linkUrl,
                               thumbnailUrl, originalUrl1, originalUrl2))
    return items

def analysis_json(js):

    items = []

    contents = json.loads(js)['contents']

    for child in contents:
        linkUrl = child['url']
        illust_id = child['illust_id']
        thumbnailUrl = child['url']

        author = child['user_name']
        browse = child['view_count']
        score = child['total_score']
        date = child['date']
        title = child['title']
        originalUrl1 = thumbnailUrl.replace('c/240x480/img-master', 'img-original')
        originalUrl2 = thumbnailUrl.replace('c/240x480/img-master', 'c/1200x1200/img-master')

        items.append(PixivItem(title, illust_id, author, date, browse, score, linkUrl,
                               thumbnailUrl, originalUrl1, originalUrl2))

    return items


def get_tt(html):
    rootSoup = BeautifulSoup(html, 'lxml')
    tt = rootSoup.select('#wrapper > footer > div > ul > li')[0].select('form > input')[1]['value']
    return tt


def download_illustration(op, items, picDir):

    print("正在下载中……")

    for item in items:
        try:
            with op.open(item.originalUrl1) as op_img1:
                if op_img1.status == 200:
                    with open(os.path.join(picDir, item.originalUrl1.split('/')[-1]), 'wb') as o:
                        o.write(op_img1.read())
                        print('插图已成功下载 -> %s' % item.get_info())
        except Exception as e:
            try:
                with op.open(item.originalUrl2) as op_img2:
                    if op_img2.status == 200:
                        with open(os.path.join(picDir, item.originalUrl2.split('/')[-1]), 'wb') as o:
                            o.write(op_img2.read())
                            print('插图已成功下载 -> %s' % item.get_info())
            except Exception as e:
                pass

        time.sleep(1)                                                                                                   # 等待1秒，爬得太快容易被发现(￣▽￣)"

def download_by_id(op, artist_id, p, picDir):
    items = None
    item_multiple = None
    visit = pixiv_url_artist + artist_id
    pg = 0
    with op.open(visit) as f:
        if f.status == 200:
            html = utils.ungzip(f.read()).decode()
            tt = get_tt(html)
            item_multiple = analysis_multiple(html, op)
            (items, pg) = analysis_html(html, False)
    if item_multiple:
        download_illustration(op, item_multiple, picDir)                                                                #下载多图
        print('本页多图部分下载完成')
    if items:
        download_illustration(op, items, picDir)                                                                        #下载单图
        print('本页下载完成')
    return pg

def download_first(op, mode, picDir):
    tt = None
    items = None
    pg = 0
    if mode in query_mode:
        visit = pixiv_url_ranking + '?' + urllib.parse.urlencode({'mode': mode})
    with op.open(visit) as f:
        if f.status == 200:
            html = utils.ungzip(f.read()).decode()
            tt = get_tt(html)
            (items, pg) = analysis_html(html, isRank)
    if items:
        download_illustration(op, items, picDir)                                                                        #下载单图
    return tt

def download_more(op, mode, p, fm, tt, picDir):
    visit = pixiv_url_ranking + '?' + urllib.parse.urlencode({
        'mode': mode,
        'p': p,
        'format': fm,
        'tt': tt
    })

    items = None

    with op.open(visit) as f:
        if f.status == 200:
            js = utils.ungzip(f.read()).decode()
            items = analysis_json(js)

    if items:
        download_illustration(op, items, picDir)


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
        query_tt = download_first(opener, query_mode[int(qmNo)], saveDir)                                               # 下载第一页插图，并获取重要参数tt
        while input("当前第%d页插图已下载完成，是否继续下载第%d页插图？"
                    "（1：是 | 其他：退出）：" % (p, p + 1)) == '1':
            p += 1
            download_more(opener, query_mode[int(qmNo)], p, query_format, query_tt, saveDir)
    elif int(type) == 1:
        print('提示：打开作者的作品页面，id=后面的那串数字就是作者的id')
        artist_id = input("请输入希望下载的作者id:")
        p_start = input('开始下载的页码数：')
        if int(p_start) > 1:
            artist_id = artist_id + '&type=all&p=' + str(p_start)
        opener = PixivLoginer.login(userid, password)
        pageCount = download_by_id(opener, artist_id, p_start, saveDir)
        p = int(p_start)
        while pageCount > p:
            p += 1
            print('准备开始下载第' + str(p) + '页')
            artist_id = artist_id + '&type=all&p=' + str(p)
            pageCount = download_by_id(opener, artist_id, p, saveDir)
    print('全部下载完啦')
    exit(0)


