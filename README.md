## [看一看妹子](http://k1kmz.com)，自动从其他网站采集妹子图，并上传微博图床，然后发布至wordpress脚本

看一看妹子网址：http://k1kmz.com

获取mm131完整数据库加群：https://jq.qq.com/?_wv=1027&k=5Djwcp4

----

## 脚本介绍

1. wb_upload 微博上传图片脚本。需在脚本**第27行**修改微博账号和密码
2. wp_db.py wordpress发布脚本。需在脚本**第26行**修改自己的wordpress网址、admin账号密码
3. ocr.py 接入第三方打码平台脚本，实现微博自动登录。 需自行注册[云打码](http://yundama.com)，然后在脚本**第10、11行**修改云打码的用户名密码
4. mm131.py 爬虫脚本；可以参考该脚本自行写爬虫入库
5. localdb.py 数据库操作脚本
6. auto_post.py 图片上传&wordpress发布脚本
7. **weibo.py 采集微博图片的脚本**

----

## 用法

0. 安装依赖包：`pip install -r requirement.txt`
1. 采集数据
    - 首先需要运行爬虫脚本，从其他网站爬取数据：`python mm131.py`
    - 采集微博图片：首先编辑`wblist.txt`，一行一个微博博主名字，然后运行：`python weibo.py`
2. 然后直接运行`auto_post.py`脚本，开始发布：`python auto_post.py`

就是这么简单


----

看一看妹子网址：http://k1kmz.com


获取mm131完整数据库加群：https://jq.qq.com/?_wv=1027&k=5Djwcp4

