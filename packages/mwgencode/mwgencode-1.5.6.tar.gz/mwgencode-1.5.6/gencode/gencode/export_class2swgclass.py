from gencode.importmdj.import_uml_models import Import_uml_models
from gencode.uml_class_models import Class,Property
from gencode.ext import Session
import os
from jinja2 import FileSystemLoader, Environment
import codecs
import json
import logging
class ExportClass2SWGClass():
    def __init__(self,source_umlfile,dest_umlfile):
        '''

        :param source_umlfile: 源umlmodel文件
        :param dest_umlfile: 汇入swg的umlmodel文件
        '''
        self.source_umlfile = source_umlfile
        self.dest_umlfile = dest_umlfile
        self.session = Session()
        tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'template')
        load = FileSystemLoader(tmp_path)
        self.env = Environment(loader=load)
        self.project = Import_uml_models(self.source_umlfile).import_model()
        self.dest_model = self._load_models(self.dest_umlfile)
        self.swg_package = self.__get_swg_package(self.dest_model)
        self.temp = self.env.get_template('swg_package_mng.tmp')

    def _load_models(self,file):
        with codecs.open(file, encoding='utf8') as f:
            js = f.read()
            return json.loads(js)

    def __get_swg_package(self,dmodel):
        for tag in dmodel.get('tags',[]):
            if tag['name']=='swagger':
                swg_ref_id = tag['reference']['$ref']
                for elem in dmodel.get('ownedElements', []):
                    if elem['_id'] == swg_ref_id:
                        return elem
        for elem in dmodel.get('ownedElements',[]):
            if elem['name']=='swagger':
                return elem
        return {}

    def __get_package_mng_code_from_temp(self, bocls):
        '''
        从模板中载入swagger 中的package
        :param bocls:
        :return:
        '''
        cls = bocls
        if getattr(bocls, "assign_propertys", None):
            cls.assign_propertys(self.session)
        codes = self.temp.render(cls_id=cls.id,
                                 swg_pkg_id=self.swg_package['_id'],
                                 cls_name=cls.name.replace(' ','').lower(),
                                 cls=cls
                                 )
        self.session.rollback()
        return codes

    def export(self,exclude_classes:list=None,include_classes:list=None):
        '''
        汇入类别到swagger，当exclude_classes,include_classes同时为None时，汇入所有的类到到swagger
        :param exclude_classes:不用汇出成swagger class的类名
        :param include_classes:只需要汇入的swagger class的类名
        :return:
        '''
        if exclude_classes is None :
            exclude_classes = []
        exclude_classes = [ecls.lower() for ecls in exclude_classes or []]
        include_classes = [ecls.lower() for ecls in include_classes or []]
        classes = self.session.query(Class). \
            filter(Class.isswagger == False). \
            filter(Class.type == 'UMLClass'). \
            filter(Class.projectid == self.project.id).all()
        classes_swg = [elm['name'] for elm in self.swg_package.get('ownedElements', []) if elm['_type'] == 'UMLClass']
        packages_swg = [elm['name'] for elm in self.swg_package.get('ownedElements', []) if elm['_type'] == 'UMLPackage']
        for cls in classes :
            class_name = cls.name.replace(' ','').lower()
            # 已产生swagger class
            if class_name in classes_swg or  '%smng'%class_name in packages_swg :
                continue
            # 有排除表时，不能产生
            if exclude_classes and  class_name in exclude_classes:
                continue
            # 有包含表时，只产生包含表的类别
            if include_classes and class_name not in include_classes:
                continue
            codes = self.__get_package_mng_code_from_temp(cls)
            self.swg_package.setdefault('ownedElements',[]).append(json.loads(codes,strict=False))
        with codecs.open(self.dest_umlfile,mode='w',encoding='utf-8') as file:
            file.write(json.dumps(self.dest_model,ensure_ascii=False))
        # 需要删除吗？？？
        # self.session.query(Project).filter(Project.id==self.project.id).delete()
        logging.info('export swagger classes success.')

    def __find_element(self,elemnts:list,key:str,value):
        '''
        查找某个元素
        :param elemnts:
        :param key:
        :param value:
        :return: obj
        '''
        for elem in elemnts:
            if elem[key]==value:
                return elem
        return None

    def export_one_swgclass(self,bocls:str):
        '''
        把bocls汇入到swagger，bocls不存在时会创建
        :param bocls:
        :return:
        '''
        cls = self.session.query(Class). \
            filter(Class.isswagger == False). \
            filter(Class.type == 'UMLClass'). \
            filter(Class.projectid == self.project.id,Class.name==bocls).first()
        if not cls :
            import uuid
            cls = Class(id=str(uuid.uuid4()),name=bocls)
            cls.propertys = [Property(id=str(uuid.uuid4()),name='id',type='integer')]
        # 获取swg中该类的package
        package_cls_swg = self.__find_element(self.swg_package['ownedElements'], 'name', '%smng' % bocls.lower())
        # 如果swagger中没有，则把模板中的package加入swagger中
        if not package_cls_swg:
            package_cls_tmp = self.__get_package_mng_code_from_temp(cls)
            self.swg_package.setdefault('ownedElements', []).append(json.loads(package_cls_tmp, strict=False))
            with codecs.open(self.dest_umlfile, mode='w', encoding='utf-8') as file:
                file.write(json.dumps(self.dest_model, ensure_ascii=False))
            logging.debug('The class (%smng) has insert' % bocls)
        else:
            logging.debug('The class (%smng) has exist'%bocls)

    def add_operation(self,swgpackage_name:str,opname:str,method:str='get'):
        '''
        在swagger类上增加一个方法
        :param swgpackage_name: swagger package 名称，如：companymng
        :param opname: companys
        :param method: http method，如：get,put,post,delete等
        :return:
        '''
        if method not in ['get','put','post','delete']:
            logging.debug("add_operation() error, the method %s not in ['get','put','post','delete']"%method)
        # 获取swg中该类的package
        package_cls_swg = self.__find_element(self.swg_package['ownedElements'], 'name',swgpackage_name)
        if not package_cls_swg:
            logging.warning('the swagger package(%s) is not exist'%swgpackage_name)
            raise ValueError('the swagger package(%s) is not exist'%swgpackage_name)
        obj_signal = self.__find_element(package_cls_swg['ownedElements'],'_type','UMLSignal')
        assert obj_signal,'the swagger package(%s) has no UMLSignal class'%swgpackage_name
        obj_cls = self.__find_element(package_cls_swg['ownedElements'],'_type','UMLClass')
        if not obj_cls:
            obj_cls = self.__find_element(package_cls_swg['ownedElements'], '_type', 'UMLDataType')
        assert obj_cls, 'the swagger package(%s) has no UMLClass class' % swgpackage_name
        # 如果方法名存在则不能产生,
        op= self.__find_element(obj_signal['operations'],'name',opname)
        if op:
            logging.error('the swagger package(%s) has a opname（%s） UMLSignal class，请修改opname再试'%(swgpackage_name,opname))
            raise ValueError('the swagger package(%s) has a opname（%s） UMLSignal class，请修改opname再试'%(swgpackage_name,opname))
        # 从模板中拷贝 物件
        import uuid
        # 使用临时的类别，保证临时物件中的id是唯一的，可以直接加入的swagger中
        cls = Class(id=str(uuid.uuid4()), name=opname)
        package_cls_tmp = json.loads(self.__get_package_mng_code_from_temp(cls), strict=False)
        obj_signal_tmp = self.__find_element(package_cls_tmp['ownedElements'], '_type', 'UMLSignal')
        op_tmp = self.__find_element(obj_signal_tmp['operations'], 'stereotype', method)
        # 与swagger建立关系
        op_tmp['_parent']['$ref']=obj_signal['_id']
        op_tmp['name'] = opname
        obj_signal['operations'].append(op_tmp)
        # 找到 in，return类
        op_parm_in = self.__find_element(op_tmp['parameters'],'name','in')
        obj_in = self.__find_element(package_cls_tmp['ownedElements'], '_id', op_parm_in['type']['$ref'])
        obj_in['_parent']['$ref']=package_cls_swg['_id']
        if method in ['post', 'put']:
            # 如果是post,put方法，则需要有一个in参数
            # 返回类型 用 obj_cls
            body_value = self.__find_element(obj_in['attributes'],'name','body')
            body_value['type']['$ref'] = obj_cls['_id']
        package_cls_swg['ownedElements'].append(obj_in)
        op_parm_return = self.__find_element(op_tmp['parameters'],'direction','return')
        obj_return = self.__find_element(package_cls_tmp['ownedElements'], '_id', op_parm_return['type']['$ref'])
        obj_return['_parent']['$ref']=package_cls_swg['_id']
        # 返回类型 用 obj_cls
        default_value = self.__find_element(obj_return['attributes'],'name','default')
        default_value['type']['$ref'] = obj_cls['_id']
        package_cls_swg['ownedElements'].append(obj_return)
        # 把in return param obj 加入到图上
        diagram_tmp= self.__find_element(package_cls_tmp['ownedElements'], '_type', 'UMLClassDiagram')
        diagram_main = self.__find_element(package_cls_swg['ownedElements'], '_type', 'UMLClassDiagram')
        op_parm_in_view = self.__find_element(diagram_tmp['ownedViews'], 'model', {"$ref": obj_in['_id']})
        op_parm_in_view['_parent']['$ref']=diagram_main['_id']
        op_parm_in_view['left'] += 380
        diagram_main['ownedViews'].append(op_parm_in_view)
        op_parm_return_view = self.__find_element(diagram_tmp['ownedViews'], 'model', {"$ref": obj_return['_id']})
        op_parm_return_view['_parent']['$ref']=diagram_main['_id']
        op_parm_return_view['left'] += 380
        diagram_main['ownedViews'].append(op_parm_return_view)
        with codecs.open(self.dest_umlfile, mode='w', encoding='utf-8') as file:
            file.write(json.dumps(self.dest_model, ensure_ascii=False))
        logging.info("add_operation(%s,%s,%s) success" % (swgpackage_name,opname,method))


if __name__ == '__main__':
    exp = ExportClass2SWGClass(r'D:\mwwork\projects\mwgencode\order_system\docs\temp.json',
                         r'D:\mwwork\projects\mwgencode\order_system\docs\temp.json')
    # exp.export()
    exp.export_one_swgclass('company')
    exp.add_operation('companymng','company2','put')