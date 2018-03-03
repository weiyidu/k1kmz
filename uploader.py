# encoding:utf8
import re
import json
import requests
import binascii
import base64
import rsa
import cStringIO as StringIO
import os
import sys
import time
from flickr import FlickrAPI
from PIL import Image
from ocr import captch
try:
    import cookielib,urllib
except:
    import http.cookiejar as cookielib
    import urllib.parse as urllib
try:
    import cPickle as pickle
except:
    import pickle


class Weibo:
    #微博账号密码
    def __init__(self,username='',password=''):
        self.cookie_file = 'wbcookies'
        self.session=requests.Session()
        self.username=username
        self.password=password
        self._login()

    def _getcode(self):
        url='https://login.sina.com.cn/cgi/pin.php?r=43100010&s=0&p=gz-9695df1a289328e23ded42c919400b59c8a9'
        r=self.session.get(url).content
        with open('verifycode.png','wb') as f:
            f.write(r)
        rimg = StringIO.StringIO(r)
        code = captch(rimg)
        return code


    def pre_login(self):
        pre_login_url = 'https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_={}'.format(time.time())
        pre_response = self.session.get(pre_login_url).text
        pre_content_regex = r'\((.*?)\)'
        patten = re.search(pre_content_regex, pre_response)
        nonce = None
        pubkey = None
        servertime = None
        rsakv = None
        if patten.groups():
            pre_content = patten.group(1)
            pre_result = json.loads(pre_content)
            nonce = pre_result.get("nonce")
            pubkey = pre_result.get('pubkey')
            servertime = pre_result.get('servertime')
            rsakv = pre_result.get("rsakv")
        return nonce, pubkey, servertime, rsakv


    def generate_form_data(self,nonce, pubkey, servertime, rsakv, username, password,with_code=False):
        rsa_public_key = int(pubkey, 16)
        key = rsa.PublicKey(rsa_public_key, 65537)
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
        passwd = rsa.encrypt(message, key)
        passwd = binascii.b2a_hex(passwd)
        username = urllib.quote(username)
        username = base64.encodestring(username)
        form_data = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'useticket': '1',
            'pagerefer': 'https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D%252F',
            'vsnf': '1',
            'su': username,
            'service': 'miniblog',
            'door': '',
            'servertime': servertime,
            'nonce': nonce,
            'pwencode': 'rsa2',
            'rsakv': rsakv,
            'sp': passwd,
            'sr': '1366*768',
            'encoding': 'UTF-8',
            'prelt': '115',
            'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META'
        }
        if with_code==True:
            form_data['door']=self._getcode()
        return form_data


    def login(self,with_code=False):
        try:
            url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'}
            nonce, pubkey, servertime, rsakv = self.pre_login()
            form_data = self.generate_form_data(nonce, pubkey, servertime, rsakv, self.username, self.password,with_code=with_code)
            req=self.session.post(url,headers=headers,data=form_data)
            redirect_result = req.content
            login_pattern = r'location.replace\(["\']*(.*?)["\']*\)'
            login_url = re.findall(login_pattern, redirect_result)[0]
            print 'login url:'+login_url
            r=self.session.get(login_url)
            r.encoding='gb2312'
            print r.text
            login_url2 = re.findall(login_pattern, r.content)[0]
            print 'login url2:'+login_url2
            r2=self.session.get(login_url2)
            cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
            with open(self.cookie_file,'wb') as f:
                pickle.dump(cookies_dict,f)
        except Exception as e:
            print(e)


    def isLogin(self):
        print 'checking if login'
        check_url='https://account.weibo.com/set/index?topnav=1&wvr=6'
        r=self.session.get(check_url)
        if r.url==check_url:
            return True
        else:
            return False

    def request_image_url(self,image_path):
        image_url = 'https://picupload.weibo.com/interface/pic_upload.php?cb=https%3A%2F%2Fweibo.com%2Faj%2Fstatic%2Fupimgback.html%3F_wv%3D5%26callback%3DSTK_ijax_1518610449473223&mime=image%2Fjpeg&data=base64&url=weibo.com%2Fu%2F6483607008&markpos=1&logo=1&nick=%40%E5%A6%B9%E5%AD%90%E8%AF%B4ok&marks=0&app=miniblog&s=rdxt&pri=null&file_source=1'
        if image_path.startswith('http'):
            headers={
                'Referer':'http://www.mm131.com/'
                ,'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
                }
            r=requests.get(image_path,headers=headers)
            img_cont=r.content
            filename=base64.b64encode(image_path)+'.'+image_path.split('/')[-1].split('.')[-1]
            with open(filename,'wb') as f:
                f.write(img_cont)
            b = base64.b64encode(open(filename,'rb').read())
        else:
            b = base64.b64encode(open(image_path,'rb').read())
        data = {'b64_data': b}
        headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}
        tourl = self.session.post(image_url,data=data,headers=headers,timeout=10).url
        image_id = re.findall('pid=(.*)',tourl)[0]
        os.remove(filename)
        return 'http://ww3.sinaimg.cn/large/%s' % image_id

    def _login(self):
        cookies_dict={}
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file,'rb') as f:
                cookies_dict=pickle.load(f)
        # rc=''
        # cookies_dict={}
        # for line in rc.split(';'):
        #     key,value=line.split('=',1)
        #     cookies_dict[key]=value
        #cookies_dict={}
        self.session.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
        if self.isLogin():
            print('load cookies and login success')
        else:
            print('load cookies but login fail')
            self.login(with_code=True)
            if not self.isLogin:
                self.login(with_code=True)
                if self.isLogin():
                    print 'login success'
                else:
                    print 'login two times and fail!'



    def get_image(self,image_path):
        url = ''
        try:
            url = self.request_image_url(image_path)
        except Exception as e:
            print(e)
            print('upload fail')
        return url



class Flickr():
    #Flickr api_key和api_secret，申请地址：https://www.flickr.com/services/apps/create/apply/
    def __init__(self,api_key='',api_secret=''):
        self.base='https://farm{farmid}.staticflickr.com/{serverid}/{id}_{secret}_o.{minetype}'
        try:
            with open('flickr.token','r') as f:
                token=pickle.load(f)
            self.flickr = FlickrAPI(api_key, api_secret,oauth_token=token['oauth_token'],oauth_token_secret=token['oauth_token_secret'])
        except:
            print 'first run!'
            f = FlickrAPI(api_key=api_key,api_secret=api_secret,callback_url='oob')
            auth_props = f.get_authentication_tokens(perms=u'write')
            auth_url = auth_props['auth_url']
            oauth_token = auth_props['oauth_token']
            oauth_token_secret = auth_props['oauth_token_secret']
            print('open the url in browser and input the code:\n'+auth_url)
            oauth_verifier=self.toUnicodeOrBust(raw_input('verifier code:'))
            f2 = FlickrAPI(api_key=api_key,api_secret=api_secret,oauth_token=oauth_token,oauth_token_secret=oauth_token_secret)
            authorized_tokens = f2.get_auth_tokens(oauth_verifier)
            final_oauth_token = authorized_tokens['oauth_token']
            final_oauth_token_secret = authorized_tokens['oauth_token_secret']
            token={'oauth_token':final_oauth_token,'oauth_token_secret':final_oauth_token_secret}
            with open('flickr.token','w') as f:
                pickle.dump(token,f)
            self.flickr = FlickrAPI(api_key=api_key,api_secret=api_secret,oauth_token=final_oauth_token,oauth_token_secret=final_oauth_token_secret)

    def toUnicodeOrBust(self,obj, encoding='utf-8'):
        if isinstance(obj, basestring):
            if not isinstance(obj, unicode):
                obj = unicode(obj, encoding)
        return obj


    def upload(self,image_path):
        if image_path.startswith('http'):
            headers={
                'Referer':'http://www.mm131.com/'
                ,'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
                }
            r=requests.get(image_path,headers=headers)
            img_cont=r.content
            filename=base64.b64encode(image_path)+'.'+image_path.split('/')[-1].split('.')[-1]
            with open(filename,'wb') as f:
                f.write(img_cont)
        else:
            filename=image_path
        try:
            with open(filename,'rb') as img:
                photo_id = self.flickr.post(files=img)
            os.remove(filename)
            return photo_id
        except Exception as e:
            print e
            os.remove(filename)
            return False

    def get_image(self,image_path):
        photo_info=self.upload(image_path)
        if photo_info==False:
            print 'upload image fail!'
            return False
        else:
            if photo_info['stat']=='ok':
                photo_id=photo_info['photoid']
                info=self.flickr.post('flickr.photos.getInfo',{'photo_id':photo_id})
                farmid=info['photo']['farm']
                serverid=info['photo']['server']
                id=info['photo']['id']
                secret=info['photo']['originalsecret']
                minetype=info['photo']['originalformat']
                imgurl=self.base.format(farmid=farmid,serverid=serverid,id=id,secret=secret,minetype=minetype)
                return imgurl
            else:
                print 'upload image fail!'
                return False







if __name__ == '__main__':
    filename = "http://img1.mm131.me/pic/2330/1.jpg"
    # wb=Weibo(username=username,password=password)
    # print(wb.get_image(filename))
    flicker=Flickr()
    imgurl=flicker.get_image(filename)
    print(imgurl)


