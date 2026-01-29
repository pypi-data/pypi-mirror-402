`rst file editor <http://rst.ninjs.org>`_

mwgencode

maxwin 团队产生工程代码的工具，uml 建模工具为starUML，工程代码包括： swagger，controller，
modules，tests code，seeds code，dockerfile，babel.cfg,uwsgi file等


maxwin 开发框架使用的 lib

1. 工具 `mwutils <https://bitbucket.org/maxwin-inc/mwutils/src>`_
2. 认证检查 `mwauth <https://bitbucket.org/maxwin-inc/auth/src>`_
3. 确定权限 `mwpermission <https://bitbucket.org/maxwin-inc/mwpermission/src>`_
4. 通用服务SDK `mwsdk <https://bitbucket.org/maxwin-inc/mwsdk/src>`_
5. aiohttp多语言 `mw-aiohttp-babel <https://bitbucket.org/maxwin-inc/mw-aiohttp-babel/src>`_
6. aiohttp认证检查和确权 `mw-aiohttp-security <https://bitbucket.org/maxwin-inc/mw-aiohttp-security/src>`_
7. aiohttpsession `mw-aiohttp-session <https://bitbucket.org/maxwin-inc/mw-aiohttp-session/src>`_
8. 认证服务 需要kong和consul，支持jwt 和session 认证
9. 确权服务 需要kong和consul


.. _gencode:

生成工程代码的方法


1. 创建工程目录，如：order_system
2. cd order_system
3. 进入cmd,在cmd 输入 ::

    gencode init -c

提示如下 ::

        gen code success!

则表示创建专案成功

4. 在pycharm中打开 order_system
5. 用 `staruml2 <http://staruml.io/download>`_ 打开(暂时不支持starUML v3) ./docs/oder_system.mdj，修改model（ `建模帮助手册 <https://docs.qq.com/doc/DQkZSaUtvWXpMU1lh>`_）
6. 在python中执行 gen_code_run.py，则可产生完整的flask专案文件


工程文件架构说明

> 目录app，为项目

- api 目录编写 swagger control 代码
- __init__.py 创建 flask app
- models.py 物件模型代码，企业物件的规则在此添加
- models_base.py 企业物件代码，由工具自动产生，无需手工维护
- unitls 增加一些工具代码

> docs 保存uml module 文件，mdj 文件为starUML v2的文件

> migrations 数据迁移文件，工具自动产生，不需要手工维护

> swagger 为swagger file 目录，工具自动产生，不需要手工维护

> tests 单元测试代码，每次增加api时，均会产生测试模板文件

> seeds 为初始化数据的代码，可视需求增减

> root 目录下的文件说明：

- config.py flask 的config 文件，包括 TestingConfig（单元测试用的config），DevelopmentConfig（开发模式下用的config），ProductionConfig（生产模式下用的config）

- docker 相关文件，docker-compose-dev.yaml(docker compose 样本，生产环境下改名成 docker-compose.yaml即可)，docker-compose.yaml（本地测试文件，不会上传git），Dockerfile

- gen_code_run.py 由工具初始化专案时产生，用于产生完整的专案代码 或 每次更新module后，重新生成专案代码

- run.py 开发环境下的run 单元， 包含 consul 和 kong 的注册

- uwsgi_run.py 生产环境下的run 单元，包含 consul 和 kong 的注册，在docker 中执行

- seed_run.py 产生系统默认数据，比如权限资料

- migrate_run.sh变更模型后，执行该文件 升级资料库，仅限开发环境

- run-dev.sh 为run.sh的模板文件

- run.sh 直接开启docker

:备注:

    1. 其中 要产生 tests 和seeds 目录，需要把test和seed 两个参数设为True，如：gen_code(include_test=True,include_seeds=True)
    2. 具体见 **readme.md**


数据迁移


  支持对开发环境下的sqlite资料的数据迁移，不建议在生产环境中执行，避免人工失误，导致损坏资料

1. install or upgrade ::

    pip install --upgrade Flask-Migrate

2. 指定Flask app

-    linux 下 ::

        export FLASK_APP=migrate_run.py

-    windows 下 ::

        set FLASK_APP=migrate_run.py

3. 初始化 ::

    flask db init

4. 产生迁移语句 ::

    flask db migrate

5. 执行升级资料库 ::

    flask db upgrade

* 可直接执行migrate_run.bat or migrate_run.sh 升级资料库

单元测试

 继承tests下的test_base.py的 BasicTestCase
 定义test 开头的单元方法，编写测试代码即可

> 代码样例

.. code-block:: python

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


> 执行单元测试 ::

    cd tests
    python run.py

升级旧专案的方法


> 如果不是由本工具产生的专案，可 参照生成代码的方法（ gencode_）

> 如果是该工具产生旧代码，可先备份代码，删除工具之前产生的代码（保留gen_code_run.py和app 目录下的除__init__.py的代码）并重现运行gen_code_run.py产生框架

