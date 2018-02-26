# coding:utf-8
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo
from wordpress_xmlrpc.methods import posts
from wordpress_xmlrpc.methods import taxonomies
from wordpress_xmlrpc import WordPressTerm
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import media, posts
import requests
import base64
import os

class Taxonomy():
    tax_list=[]
    tax_dict={}

    def __existsattr__(self, attrname):
        exists = attrname in self.tax_list
        return exists



class WPDB():
    #修改你的网站，还有admin账号密码
    def __init__(self, site='http://domain.com', user='', passwd=''):
        self.wp = Client('{}/xmlrpc.php'.format(site), user, passwd)
        self.categories = Taxonomy()  # self.wp.call(taxonomies.GetTerms('category'))
        self.tags = Taxonomy()  # self.wp.call(taxonomies.GetTerms('post_tag'))
        _cat=self.wp.call(taxonomies.GetTerms('category'))
        _tag=self.wp.call(taxonomies.GetTerms('post_tag'))
        [self.categories.tax_list.append(i.name) for i in _cat]
        [self.tags.tax_list.append(i.name) for i in _tag]
        for i in _cat:
            self.categories.tax_dict.setdefault(i.name,i.taxonomy_id)
        for i in _tag:
            self.tags.tax_dict.setdefault(i.name,i.taxonomy_id)

    def _insert(self, name, slug=None, type='category', parentid=None):
        cat = WordPressTerm()
        cat.taxonomy = type
        cat.name = name  # 分类名称
        cat.parent = parentid  # 父分类
        cat.slug = slug  # 分类别名，可以忽略
        taxid = self.wp.call(taxonomies.NewTerm(cat))  # 新建分类返回的id
        if type == 'category':
            self.categories.tax_list.append(name)
            self.categories.tax_dict.setdefault(name,taxid)
        else:
            self.tags.tax_list.append(name)
            self.tags.tax_dict.setdefault(name,taxid)

    def _find_media(self,filename):
        try:
            fid=self.wp.call(media.GetMediaLibrary(filename))[0].id
        except:
            fid=False
        return fid

    # type:category,post_tag
    def get_or_insert_tax(self, name, type='category', slug=None, parent=None, parent_slug=None):
        """
        查询是否存在类别/标签,若不存在则创建一个
        :type:元素类别，category文章分类,tag标签
        :name:元素名
        :slug:别名[可选]，创建时用
        :parent:父元素名[可选]，创建时用
        :parent_slug:父元素别名[可选]，创建时用
        """
        taxid = None
        if type == 'category':
            tax = self.categories
        else:
            tax = self.tags

        if tax.__existsattr__(name):
            print(u'tax {} alright exists'.format(name))
            taxid = tax.tax_dict[name]
        else:
            print(u'tax {} do not exists'.format(name))
            if parent is None:
                self._insert(name=name, slug=slug, type=type)
            else:
                if self.get_or_insert_tax(parent) is None:
                    self._insert(name=parent, slug=parent_slug, type=type)
                else:
                    parentid = tax.tax_dict[parent]
                    self._insert(name=name, slug=slug,type=type, parentid=parentid)
            taxid=self.get_or_insert_tax(name)
        return taxid

    def upload_picture(self,filepath,name=None,mimetype=None):
        print filepath
        if name is None:
            name=filepath.split('/')[-1]
        if mimetype is None:
            _=name.split('.')[-1]
            mimetype='image/{}'.format(_)
        filename=filepath
        if filepath.startswith('http'):
            headers={
                'Referer':'http://www.mm131.com/'
                ,'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'
                }
            r=requests.get(filepath,headers=headers)
            img_cont=r.content
            filename=base64.b64encode(filepath)+'.'+filepath.split('/')[-1].split('.')[-1]
            with open(filename,'wb') as f:
                f.write(img_cont)
        data = {
            'name': name,
            'type': mimetype,  # mimetype
        }
        try:
            with open(filename, 'rb') as img:
                data['bits'] = xmlrpc_client.Binary(img.read())
            response = self.wp.call(media.UploadFile(data))
            attachment_id = response['id']
        except Exception as e:
            attachment_id=None
        os.remove(filename)
        return attachment_id


    def create_post(self,title,content,post_format='image',tag=None,category=None,thumbnail=None,thumnnail_path=None):
        post = WordPressPost()
        post.title = title
        post.content = content
        post.comment_status = 'open'
        post.post_format = post_format  # image,video,0
        post.post_status = 'publish'  # 文章状态，不写默认是草稿，private表示私密的，draft表示草稿，publish表示发布
        post.terms_names = {
            'post_tag': tag #['test', 'beauty'],  文章所属标签，没有则自动创建
            ,'category': category #['校园美女']  文章所属分类，没有则自动创建
        }
        if thumnnail_path.startswith('http'):
            post.thumbnail=self.upload_picture(thumnnail_path)
        else:
            post.thumbnail = self._find_media(thumnnail_path)  # 缩略图的id
        try:
            self.wp.call(posts.NewPost(post))
        except Exception as e:
            print e







if __name__=='__main__':
    wp = WPDB(site='http://domain', user='', passwd='')
    wp.upload_picture('http://img1.mm131.me/pic/905/m905.jpg')
