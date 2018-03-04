#-*- coding=utf-8 -*-
import requests
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from threading import Thread
from Queue import LifoQueue
from localdb import DB

host='http://www.mm131.com'
parent='mm131'
list_pattern={
        u'性感美女':{'page1':'/xinggan/','page':'/xinggan/list_6_{page}.html','slug':'xinggan'}
        ,u'清纯美女':{'page1':'/qingchun/','page':'/qingchun/list_1_{page}.html','slug':'qingchun'}
        ,u'大学校花':{'page1':'/xiaohua/','page':'/xiaohua/list_2_{page}.html','slug':'xiaohua'}
        ,u'性感车模':{'page1':'/chemo/','page':'/chemo/list_3_{page}.html','slug':'chemo'}
        ,u'明星写真':{'page1':'/mingxing/','page':'/mingxing/list_5_{page}.html','slug':'mingxing'}
        ,u'旗袍美女':{'page1':'/qipao/','page':'/qipao/list_4_{page}.html','slug':'qipao'}
        }
cate_dict={}
for key in list_pattern:
    cate_dict[list_pattern[key]['slug']]=key
headers={
    'Referer':'http://www.mm131.com/'
    ,'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
    }
img_base='http://img1.mm131.me/pic/{pid}/{subid}.jpg'
detail_regex=re.compile('<dd><a target="_blank" href="(http://www.mm131.com/.*?/\d+?\.html)"><img src="http://img1.mm131.me/pic/\d+?/0.jpg" alt="(.*?)"')
id_reg=re.compile('http://www\.mm131\.com/.*?/(\d+?)\.html')
subid_reg=re.compile('http://img1\.mm131\.me/pic/\d+?/(\d+)\.jpg')
max_page_reg=re.compile(u'<div class="content-page"><span class="page-ch">.*?(\d+).*?</span>')

def get_max_page(cate):
    url=host+cate
    r=requests.get(url)
    pages=re.findall('''<a href='list_\d+_(\d+)\.html' class="page-en">''',r.text)
    pages=map(int,pages)
    max_page=max(pages)
    return max_page


def get_pid(url):
    global result_queue
    slug=re.findall('http://www.mm131.com/(.*?)/',url)[0]
    cate=cate_dict[slug]
    print 'try to parse url {},slug {}'.format(url,slug)
    try:
        r=requests.get(url,headers=headers)
        r.encoding='gb2312'
        content=r.text
        details=detail_regex.findall(content)
        for detail in details:
            result_queue.put(detail+(cate,))
    except Exception as e:
        print(e)


def get_max_subid(url):
    try:
        r=requests.get(url,headers=headers)
        max_page=int(max_page_reg.findall(r.content)[0])
        return max_page
    except Exception as e:
        print(e)
        return False


if __name__=='__main__':
    post_db=DB('Post')
    picture_db=DB('Picture')
    url_queue=LifoQueue()
    result_queue=LifoQueue()
    if len(sys.argv)==1:
        for key in list_pattern.keys():
            url_queue.put(host+list_pattern[key]['page1'])
    else:
        for key in list_pattern.keys():
            max_page=get_max_page(list_pattern[key]['page1'])
            url_queue.put(host+list_pattern[key]['page1'])
            for page in range(2,max_page+1):
                url_queue.put((host+list_pattern[key]['page']).format(page=page))
    print('{} pages waiting for parse'.format(url_queue.qsize()))
    tasks=[]
    while 1:
        url=url_queue.get()
        t=Thread(target=get_pid,args=(url,))
        tasks.append(t)
        if url_queue.empty():
            break
    for task in tasks:
        task.start()
    for task in tasks:
        task.join()
    while 1:
        url,title,cate=result_queue.get()
        id=id_reg.findall(url)[0]
        poster='http://img1.mm131.me/pic/{}/0.jpg'.format(id)
        post_db.insertnew(id=id,name=title,poster=poster,category=cate,tags=cate,status=False)
        max_subid=get_max_subid(url)
        if max_subid!=False:
            for subid in range(1,max_subid+1):
                subid=int(subid)
                print('insert new item : post id {} , subid: {}'.format(id,subid))
                pic=img_base.format(pid=id,subid=subid)
                picture_db.insertnew(pid=id,subid=subid,url=pic)
        if result_queue.empty():
            break

