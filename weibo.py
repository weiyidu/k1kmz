# -*- coding: utf-8 -*-
import os
import sys
import locale
import json
import re
import time
import requests
import threading
import datetime
from localdb import DB

try:
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning)
except:
    pass

try:
    reload(sys)
    sys.setdefaultencoding('utf8')
except:
    pass

try:
    input = raw_input
except NameError:
    pass

IS_PYTHON2 = sys.version[0] == "2"
SYSTEM_ENCODE = sys.stdin.encoding or locale.getpreferredencoding(True)
USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
PIC_AMOUNT = 0
total = 0
containerid=0
SAVE_PATH = ""
pictures = {}
post_db=DB('Post')
picture_db=DB('Picture')
id_db=DB('ID')

def print_fit(string, flush=False):
    if IS_PYTHON2:
        string = string.encode(SYSTEM_ENCODE)
    if flush == True:
        sys.stdout.write("\r" + string)
        sys.stdout.flush()
    else:
        sys.stdout.write(string + "\n")


def requests_retry(url, max_retry=0):
    retry = 0
    while True:
        if retry > max_retry:
            return
        try:
            response = requests.request(
                "GET", url, headers={"User-Agent": USER_AGENT}, timeout=5, verify=False)
            return response
        except:
            retry = retry + 1


def uid_to_containerid(uid):
    if re.search(r'^\d{10}$', uid):
        return "107603" + uid


def nickname_to_containerid(nickname):
    url = "https://m.weibo.com/n/{}".format(nickname)
    response = requests_retry(url=url)
    uid_check = re.search(r'(\d{16})', response.url)
    if uid_check:
        return "107603" + uid_check.group(1)[-10:]


def get_pic_and_video(card):
    global pictures
    if 'mblog' in card.keys():
        blog = card['mblog']
        try:
            posttime = datetime.datetime.strptime(
                blog['created_at'], '%Y-%m-%d').strftime('%Y%m%d')
        except:
            try:
                year = str(datetime.datetime.now().year)
                posttime = datetime.datetime.strptime(
                    year + '-' + blog['created_at'], '%Y-%m-%d').strftime('%Y%m%d')
            except:
                posttime=datetime.datetime.now().strftime('%Y%m%d')
        description = ''.join(re.findall(u'[\u4e00-\u9fa5]',blog['text']))
        pid=blog['id']
        if int(posttime)>=20171001:
            if 'retweeted_status' in blog.keys():
                if "pics" in blog["retweeted_status"]:
                    pictures.setdefault(posttime,[])
                    for pic in blog["retweeted_status"]["pics"]:
                        if "large" in pic:
                            picture = pic["large"]["url"]
                            pictures.setdefault(posttime,[]).append(picture)
                # elif "page_info" in blog["retweeted_status"]:
                #     if "media_info" in blog["retweeted_status"]["page_info"]:
                #         video = blog["retweeted_status"]["page_info"]["media_info"]["stream_url"]
                #         poster = blog["retweeted_status"]["page_info"]["page_pic"]["url"]
                #         videos.append((pid,posttime, description, poster, video))
            else:
                if "pics" in blog:
                    pictures.setdefault(posttime,[])
                    for pic in blog["pics"]:
                        if "large" in pic:
                            picture = pic["large"]["url"]
                            pictures.setdefault(posttime,[]).append(picture)
                # elif "page_info" in blog:
                #     if "media_info" in blog["page_info"]:
                #         video = blog["page_info"]["media_info"]["stream_url"]
                #         poster = blog["page_info"]["page_pic"]["url"]
                #         videos.append((pid,posttime, description, poster, video))


def parse_url(url):
    response = requests_retry(url=url, max_retry=3)
    json_data = response.json()
    try:
        cards = json_data["data"]["cards"]
        for card in cards:
            get_pic_and_video(card)
    except Exception as e:
        print(e)
        print('empty')

def get_img_urls(containerid):
    global pictures
    global total
    id = id_db.select(table='ID',id=containerid)[0]
    page = 1
    amount = 0
    url = "https://m.weibo.cn/api/container/getIndex?count={}&page={}&containerid={}".format(
        25, 1, containerid)
    response = requests_retry(url=url, max_retry=3)
    json_data = response.json()
    total = json_data["data"]["cardlistInfo"]["total"]
    if id is None:
        pages = int(round(total / 25.0, 0))
    elif id.postnum is None:
        pages = int(round(total / 25.0, 0))
    else:
        pages = int(round((total - id.postnum) / 25.0, 0))
    urls = ["https://m.weibo.cn/api/container/getIndex?count={}&page={}&containerid={}".format(
        25, i, containerid) for i in range(1, pages + 1)]
    threads = []
    for url in urls:
        t = threading.Thread(target=parse_url, args=(url,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print_fit("\n分析完毕,图片数 {}".format( len(pictures.items())))



def write(name,containerid):
    global pictures
    for k,picture in pictures.items():
        id=str(containerid)+str(k)
        title=u'微博采集-'+name+'-'+str(k)
        cate=u'微博'
        tags=name
        poster=picture[0]
        post_db.insertnew(id=id,name=title,poster=poster,category=cate,tags=tags,status=False)
        for idx,url in enumerate(picture):
            sys.stdout.write('weibo {} day {} insert {} picture\r'.format(name,k,idx))
            sys.stdout.flush()
            data=picture_db.insertnew(pid=id,subid=idx,url=url)


def main(name):
    global containerid
    global total
    containerid = nickname_to_containerid(name)
    #containerid = name
    get_img_urls(containerid)
    if id_db.select(table='ID',id=containerid)[0]==None:
        id_db.insertnew(id=containerid,postnum=total)
    else:
        id_db.update(id=containerid,postnum=total)
    write(name,containerid)


if __name__ == "__main__":
    #name = sys.argv[1]
    #name = unicode(name.strip())
    #main(name)
    namelist=[]
    with open('wblist.txt','r') as f:
        for name in f.readlines():
            namelist.append(unicode(name.strip()))
    for name in namelist:
        print 'start crawler weibo user:{}'.format(name)
        main(name)
