$env:SECRET_KEY = ""
# 邮箱相关
$env:MAIL_USERNAME = ''
$env:MAIL_PASSWORD = ''
$env:FLASKY_ADMIN = ''
# 数据库相关
$database_name = ""
$env:DEV_DATABASE_URL = "" + $database_name
$env:TEST_DATABASE_URL = "" + $database_name
$env:DATABASE_URL = "" + $database_name
