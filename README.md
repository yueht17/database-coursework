# 基于flask的微沙龙论坛
* ****
## 0.Coursework Assignment
WeSalon is a brand-new mode for Online to Offline academic discussions. 

With the help of this tool, students can publish the discussion activity online and communicate
with academic partners offline. 

Specifically, a student can apply for an activity at a certain place, list all the activities,
participate in an activity and make some comments on a held activity.
 
You are required to design a corresponding database to support the normal operations of the WeSalon
system.

### 0.1 Assumptions
- There are three status of the activities, which are reserved,ongoing, finished.

- Each activity must be held in a certain place over a period of time. 
Therefore, activities cannot be overlapped.

### 0.2 Tasks
- Design a database for the WeSalon system that allows students to
  - Manage the activities;
  - Update (modify/delete) the status of the activities.
  - Display each status of the activities separately.
  - Apply for an activity;(each activity has its own capacity, please note the possible conflicts with previously reserved places or time)

  - Participate in an activity; (a student can participate in an activity if there are no
  conflicts with other participated activities and the current participation number is
  below the activity capacity)

  - Comment on an activity; (a student can only comment on an activity iff he/she
  has participated in the activity and the activity has been finished)

  - Filter the activities. (e.g. sort the reserved activities that will hold English Corner
  ascending by the start time and descending by the activity capacities. You can filter
  any type of activities as you like)

  - Code a demo programme to implement the system
  You can use any language for programming, and any kind of GUI
  is acceptable.

* ****
## 1.部署（所用系统ubuntu18.04）
### 1.1 安装相关依赖性
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-dev nginx git postgresql postgresql-contrib  python-psycopg2 libpq-dev
sudo pip3 install virtualenv
```
### 1.2 克隆源代码
```bash
git clone https://github.com/yueht17/database-coursework.git
```
### 1.3 创建虚拟环境
```bash
virtualenv ./database-coursework/ && cd ./database-coursework
source ./bin/activate
pip3 install -r ./requirements.txt
pip3 install gunicorn
```
### 1.4 导入相关环境变量
```bash
export PYTHONUNBUFFERED="1"
export SECRET_KEY=""
export MAIL_USERNAME=""  # 主要stmp的邮箱的端口号：25
export MAIL_PASSWORD=""
export FLASKY_ADMIN=""
# 注意如果不使用pgsql，系统默认会创建sqlite数据库，所以以下变量为optional
export DEV_DATABASE_URL=""
export TEST_DATABASE_URL=""
export DATABASE_URL=""
```
### 1.5 数据库相关的操作<在此之前确保数据库连接成功>
```bash
python ./manage.py db init
python ./manage.py db migrate
python ./manage.py db upgrade
python ./manage.py generate_fake
```
### 1.6 配置gunicorn
```bash
sudo vim /etc/systemd/system/myproject.service
# 配置文件如下
[Unit]
Description=Gunicorn instance to serve myproject
After=network.target
[Service]
User=root # 注意这里是你的用户名
Group=www-data
WorkingDirectory=/root/database-coursework
Environment="PATH=/root/database-coursework/bin" "SECRET_KEY=" "MAIL_USERNAME=" "MAIL_PASSWORD=" "FLASKY_ADMIN="
ExecStart=source /root/database-coursework/var.sh &&/root/database-coursework/bin/python /root/database-coursework/bin/gunicorn --workers 3 -b 127.0.0.1:8080 -m 007 manage:app
[Install]
WantedBy=multi-user.target
# guinicorn的操作方法
sudo systemctl start myproject
sudo systemctl stop myproject
sudo systemctl enable myproject
sudo systemctl status myproject 
```

### 1.7 nginx配置
```bash
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.bak
sudo vim /etc/nginx/sites-available/default
# 配置文件如下：
server {    
    server_name  45.77.132.121; 
    location / {
        proxy_pass http://127.0.0.1:8080; 
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
  }
# nginx的操作方法
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl enable nginx
sudo systemctl status nginx 
```
### 1.8 启动
```bash
sudo systemctl start nginx
sudo systemctl start myproject
```
* ****
## 2. 文件目录
```bash
.
├── app
│   ├── auth # 用于认证和登录的模块
│   │   ├── forms.py
│   │   ├── __init__.py
│   │   └── views.py
│   ├── decorators.py # 一些函数修饰器
│   ├── email.py # 用于发送email
│   ├── __init__.py
│   ├── main 
│   │   ├── errors.py
│   │   ├── forms.py # 表单
│   │   ├── __init__.py
│   │   └── views.py # 视图函数
│   ├── models.py # 数据模型
│   ├── static # css和ico 静态文件
│   │   ├── favicon.ico
│   │   └── styles.css
│   └── templates # 相关网页的模板
│       ├── 403.html
│       ├── 404.html
│       ├── 500.html
│       ├── _activities.html
│       ├── activity.html
│       ├── auth
│       │   ├── change_email.html
│       │   ├── change_password.html
│       │   ├── email
│       │   │   ├── change_email.html
│       │   │   ├── change_email.txt
│       │   │   ├── confirm.html
│       │   │   ├── confirm.txt
│       │   │   ├── reset_password.html
│       │   │   └── reset_password.txt
│       │   ├── login.html
│       │   ├── register.html
│       │   ├── reset_password.html
│       │   └── unconfirmed.html
│       ├── base.html
│       ├── _comments.html
│       ├── edit_activity.html
│       ├── edit_profile.html
│       ├── followers.html
│       ├── index.html
│       ├── _intro.html
│       ├── _macros.html
│       ├── mail
│       │   ├── new_user.html
│       │   └── new_user.txt
│       ├── moderate.html
│       ├── publish.html
│       └── user.html
├── config.py # 相关的配置文件
├── LICENSE
├── requirements.txt
├── manage.py # 项目的管理脚本
├── README.md
├── SetEnvVar.ps1 # 用于powerhsell配置环境变量的脚本
└── tests # 测试模块
    ├── __init__.py
    ├── test_basics.py
    └── test_user_model.py
``` 