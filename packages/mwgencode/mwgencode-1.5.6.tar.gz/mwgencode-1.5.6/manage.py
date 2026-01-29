from typing import TextIO
import logging
from gencode.gen_code import GenCode,GenProject_Sample,GenProject_Flask,GenProject_Aiohttp,GenSwagger
from gencode.importmdj.import_swagger2_class import  ImportSwagger
import argparse
import os
import sys
from gencode.gencode.export_class2swgclass import ExportClass2SWGClass
import yaml
import gencode.upgrade as upgrade
class Gen_Code():
    def __init__(self,args):
        # project 类型，flask，aiohttp
        # self.type = type
        # self.umlfile = os.path.abspath(umlfile)
        # self.rootpath = os.path.abspath(rootpath)
        self.args = args
        self.prj_conf = None

    def _get_config(self) -> dict:
        def load_config():
            cnfgfile = os.path.join(os.path.abspath(self.args.root_path), 'gen_code.yaml')
            if not os.path.exists(cnfgfile):
                raise Exception('gen_code.yaml文件不存在，请先执行 gencode init 初始化项目！')
            yml = open(cnfgfile)
            try:
                self.prj_conf = yaml.full_load(yml)
            except Exception as e:
                raise Exception('载入 gen_code.yaml 出错，error:%s' % e)
            return self.prj_conf
        if self.prj_conf is None:
            self.prj_conf  = load_config()
        return self.prj_conf

    def _get_apptype(self):
        try:
            return self._get_config().get('project', {}).get('type', 'flask')
        except Exception as e:
            raise Exception('gen_code.yaml 文件内容出错，%s' % e)

    def _get_rootpath(self):
        try:
            # cmd有指定rootpath 时，以指定的rootpath
            return self.args.root_path if self.args.root_path!='.' else self._get_config().get('project',{}).get('rootpath','.')
        except Exception as e:
            raise Exception('gen_code.yaml 文件内容出错，%s'%e)

    def _get_umlfile(self):
        try:
            return os.path.join(self._get_rootpath(),
                                   self._get_config()['project']['doc_dir'],
                                   self._get_config()['project']['models']['main']['file'])
        except Exception as e:
            raise Exception('gen_code.yaml 文件内容出错，%s'%e)

    def init_project(self):
        '''
        产生一个包含 sample.mdj文件和gen_code_run.py单元的专案
        :return:
        '''
        gp = GenProject_Sample(r'%s' % self.args.umlfile,
                        r'%s' % self.args.project_name)
        gp.gen_code(self.args.python_code)


    def gen_export(self):
        umlfile = self._get_umlfile()
        swg = GenSwagger(umlfile)
        swg.export_one_swgclass(self.args.umlclass,umlfile)

    def gen_add(self):
        umlfile = self._get_umlfile()
        swg = GenSwagger(umlfile)
        swg.add_operation(self.args.swagger_package, self.args.umlclass_operation, self.args.http_method_type)
 
    def gen_build(self):
        prj_type = self._get_apptype()
        umlfile = self._get_umlfile()
        prj_rootpath = self._get_rootpath()
        if prj_type =='flask':
            gp = GenProject_Flask(r'%s' % umlfile,
                                  r'%s' % prj_rootpath)
        elif prj_type =='aiohttp':
            gp = GenProject_Aiohttp(r'%s' % umlfile,
                                    r'%s' % prj_rootpath)
        else:
            raise Exception('不支持该project type(%s)'%prj_type)
        gp.gen_code()
        g = GenCode(umlfile, prj_rootpath)
        # 产生model
        g.model()

    def gen_upgrade(self):
        # logging.info(self.args)
        dir = self.args.dir
        umlfile = self._get_umlfile()
        swg = ImportSwagger().impUMLModels(umlfile)
        if self.args.type=='k8s':
            k8s = upgrade.Upgrade_k8s(dir,swg)
            k8s.merge_code()

def main():
    parser = argparse.ArgumentParser(description='''产生flask web框架的代码''')
    parser.add_argument('-r', '--root-path',
                           help='专案的根目录(default: 当前目录名)',
                           default='.')
    subparsers = parser.add_subparsers(title='Command')

    # 初始项目，建立sample umlmodel，config等文件
    gp_parser = subparsers.add_parser('init', help='创建项目的初始文件，包括uml，cconfig等文件', add_help=True)
    gp_parser.set_defaults(command='init_project')
    gp_parser.add_argument('-f', '--umlfile',
                        type = str,
                        help='指定mdj文件 (default: sample.mdj)，不指定时以项目名为文件名',
                        default='default.mdj')
    gp_parser.add_argument('-p', '--project-name',
                        help='专案名称(default: 当前目录名)',
                        default='.')
    gp_parser.add_argument('-t', '--project-type',
                        help='专案类型 ：flask，aiohttp，default为 flask',
                        type=str, choices=['flask', 'aiohttp'],
                        default='flask')
    gp_parser.add_argument('-c', '--python-code',
                        help='产生gen_code_run.py 单元',
                        action='store_true')

    gp_parser = subparsers.add_parser('build', help='产生项目相关的文件,UMLmodel或gen_code.yaml有变更时,需要重新执行,以生成代码'
                                                 '-m model名称', add_help=True)
    gp_parser.set_defaults(command='gen_build')
    # gp_parser.add_argument('-m','--model', help='model名称',type=str,default = 'main')

    gp_parser = subparsers.add_parser('add', help='添加一个方法到swagger相关类', add_help=True)
    gp_parser.set_defaults(command='gen_add')
    # gp_parser.add_argument('-m','--model', help='model名称,暂',type=str)
    gp_parser.add_argument('-p','--swagger_package', help='swagger package class名称,如:employeemng',type=str)
    gp_parser.add_argument('-o','--umlclass_operation', help='uml class的operation名称,如: get_employee',type=str)
    gp_parser.add_argument('-t','--http_method_type', help='操作类别,如:get,post,put,delete',type=str,default='get')

    gp_parser = subparsers.add_parser('exp', help='把logic view中的umlclass 生成 swagger class,包含 get,post,put,delete 的operation', add_help=True)
    gp_parser.set_defaults(command='gen_export')
    gp_parser.add_argument('-c','--umlclass', help='logic view中的uml class 名称, 如:employee',type=str)

    gp_parser = subparsers.add_parser('upgrade', help='升级项目相关的文件,如:k8s'
                                                 '-t 升级类型名称', add_help=True)
    gp_parser.set_defaults(command='gen_upgrade')
    gp_parser.add_argument('-t','--type',
                           help='升级类型的名称,如:k8s',
                           type=str,
                           default = 'k8s')
    gp_parser.add_argument('-d', '--dir',
                           help='专案目录(default: 当前目录名)',
                           default='.')

    if len(sys.argv)==1:
        parser.print_help()
        print('一)  初始化专案的命令')
        print('     gencode init -h   # 查看命令帮助,所有参数都可以独立使用,也可以组合使用')
        print('     gencode init      # 产生一个以当前目录名为专案名称的flask项目, 如果想修改专案参数, 请直接修改gen_code.yaml文件')
        print('     gencode init -p drts-order -t flask   # 产生一个专案名称为drts-order 的flask项目')
        print('     gencode init -c  # 产生gen_code_run.py单元')
        print('二)  产生专案所有的命令,有变更model或配置时时,需要重新执行,以生成代码:')
        print('     gencode build  # 按gen_code.yaml文件,产生项目的所有文件')
        print('三)  根据类名生成swagger class,需要在staruml中 执行 reload ')
        print('     gencode exp -h   # 查看命令帮助,所有参数都可以独立使用,也可以组合使用')
        print('     gencode exp -c employee  # 把logic view中的employee 生成 swagger class,包含 get,post,put,delete 的operation')
        print('四)  给swagger class 增加一个操作(operation),需要在staruml中 执行 reload ')
        print('     gencode add -h   # 查看命令帮助,所有参数都可以独立使用,也可以组合使用')
        print('     gencode add -p employeemng -o get_employee -t get  # 给swagger class employeemng 增加一个get_employee的操作,操作类型为get')
        print('五)  升级代码,如: 支持 k8s')
        print('     gencode upgrade -h   # 查看命令帮助,所有参数都可以独立使用,也可以组合使用')
        print('     gencode upgrade -t k8s   # 升级旧专案支持 k8s')        
        print('备注: 当不是在当前项目的根目录执行时,需要指定rootpath参数,如:')
        print('     gencode -r ./mwwork/projects/drts-order build  ')
        print('     gencode -r ./mwwork/projects/drts-order exp -c employee  ')
        print('     gencode -r ./mwwork/projects/drts-order  add -p employeemng -o get_employee -t get' )
        sys.exit()
    args = parser.parse_args(sys.argv[1:])
    print(args)
    gen_code = Gen_Code(args)
    getattr(gen_code, args.command)()
    print('gen code success!')

if __name__ == '__main__':
    # 设置环境变量
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) == 1:
        # 调试时使用的默认参数
        # sys.argv.extend(['init', '-p', 'testproject', '-t', 'flask','-c'])
        sys.argv.extend(['-r','./testproject','build'])
        # sys.argv.extend(['-r','./testproject','exp','-c','order'])
        # sys.argv.extend(['-r','./testproject','add','-p','ordermng','-o','delete_orders','-t','delete'])
        # sys.argv.extend(['upgrade','-d','./testproject'])
    main()
 