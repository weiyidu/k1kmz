#-*- coding=utf-8 -*-
from uploader import *
from wp_db import *
from localdb import *
import StringIO
import sys
import datetime

tc='flickr' #选择图床，flickr:flickr图床，weibo:微博图床
if tc=='weibo':
    upload=Weibo()
else:
    upload=Flickr()
wp = WPDB()
#wp.create_post(title='测试',content='ojbk',tag=['test','ojbk'],category=['test'],thumbnail='122.png')
local=DB('Post')



timenow=lambda :datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log(msg):
    print u'{} - {}'.format(timenow(),msg)


def postnew():
    post,pictures=local.get_a_item()
    if post is None:
        log('get no post!')
        return False
    content=''
    title=post.name
    category=post.category.split(',')
    tag=post.tags.split(',')
    #thumbnail=post.poster
    log(u'try to post a new post,title {}'.format(title))
    total=len(pictures)
    i=0
    thumnnail_path=None
    for picture in pictures:
        if 'sinaimg.cn' in picture.url:
            wb_img_url=picture.url
        else:
            wb_img_url=upload.get_image(picture.url)
        content+='\n<img class="alignnone size-medium wp-image-42" src="{pic}" alt="" width="600" height="100%" />'.format(pic=wb_img_url)
        if thumnnail_path is None:
            thumnnail_path=wb_img_url
        i+=1
        sys.stdout.write('upload {}/{}\r'.format(i,total))
        sys.stdout.flush()
    wp.create_post(title=title,content=content,tag=tag,category=category,thumnnail_path=thumnnail_path)
    local.update(id=post.id,status=True)


if __name__=='__main__':
    while 1:
        try:
            if tc=='weibo':
                upload._login()
            name=postnew()
            if name==False:
               time.sleep(60*60)
            else:
                log('{} create new posts success!'.format(timenow()))
                time.sleep(5)
        except Exception as e:
            log('error :'+str(e))
            time.sleep(60*60)


