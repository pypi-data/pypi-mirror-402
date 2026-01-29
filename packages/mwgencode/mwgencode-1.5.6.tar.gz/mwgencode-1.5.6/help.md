### 内容
根据starUML 的uml 模型产生python代码的工具，如： swagger，ctroller，modules等代码
###产生分发包
```bash
python setup.py sdist
twine upload dist/*

```

###安装方式
```bash
pip install mwgencode --upgrade
```
```bash
pip install git+https://maxwin_ch@bitbucket.org/maxwin-inc/gencode.git
```

###生成flask代码的方法
1. 创建工程目录，如：order_system
2. cd order_system
3. 进入cmd,在cmd 输入：
```bash
gencode gsp 
```
提示如下，则表示创建专案成功
```bash
gen code success!

```
4. 在pycharm中打开 order_system
5. 用staruml2打开 ./docs/oder_system.mdj，修改model
6. 在python中执行 gen_code_run.py，则可产生完整的flask专案文件

### 数据迁移
> 支持对开发环境下的sqlite资料的数据迁移，不建议在生产环境中执行，避免人工失误，导致损坏资料
1. install or upgrade
```bash
pip install --upgrade Flask-Migrate
```
2.指定Flask app
> linux 下
```bash
export FLASK_APP=app.py
```
> windows 下
```bash
set FLASK_APP=app.py
```
3. 初始化
```bash
flask db init
```
4. 产生迁移语句
```bash
flask db migrate
```
5. 执行升级资料库
```bash
flask db upgrade
```

### 单元测试
> 继承tests下的test_base.py的 BasicTestCase
> 定义test 开头的单元方法，编写测试代码即可
> 代码样例
```python
from .test_base import BasicTestCase
from app.models import *
from app import db
class Testexp(BasicTestCase):
    # 测试model
    def test_data1(self):
        cet = Cacl_exp_type()
        cet.code = 'cet001'
        cet.description = 'cet_des001'
        db.session.add(cet)
        db.session.commit()
        cet = Cacl_exp_type.query.first()
        self.assertEqual(cet.code,'cet001')
    
    # 测试方法
    def test_health(self):
        response = self.client.get(self.url_for('health'))
        self.assertTrue(response.status_code, 200)
```

> 执行单元测试
```bash
cd tests
python run.py
```

### 多语言 flask-babel支持
1. app/__init__.py 中增加 代码
```python
...
from flask import request

from flask_babel import Babel
...
babel = Babel()

def create_app_swagger(config_name):
...
    babel.init_app(app)
...

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['zh', 'tw', 'en'])
```
2. 代码单元增加翻译 _()
```python
from flask_babel import gettext as _
...
def roles_id_delete(id,jwt = None):
    ...
    if auth_user.manageuser and role.issystem:
        raise Exception(_('只有超级用户才能删除系统role！'))
```

#### 升级对session auth type的支持 （auth已同时支持session和JWT认证，authtype不需要设定了）  
a. 在__init__.py中增加代码   
````python
from mwauth import auth,AuthType
from mwauth.redis_session import RedisSessionInterface
...
auth = auth(config['default'].AUTH_TYPE)
...
def create_app_swagger(config_name):
    ...
    app.session_interface = RedisSessionInterface(app, rds)
````
b. config.py 中增加 AUTH_TYPE 定义   
```python
from mwauth import AuthType
...
class DevelopmentConfig(Config):
    ...
    AUTH_TYPE = AuthType.jwt.value
```

c. run.py  增加不注册kong的判断
```python
from mwauth import AuthType
...
def register_service(config_name,app):
    from config import config
    # 注册本服务到kong
    config =  config[config_name]
    if config.AUTH_TYPE!=AuthType.kong_jwt.value:
        return
```   
d. 修改 utils.py的 get_login_user，p_check
> 同时支持jwt 和session 获取服务

e. docker 文档增加 AUTH_TYPE 环境变量

