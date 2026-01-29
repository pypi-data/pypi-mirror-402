# -*- coding: utf-8 -*-

from icemammoth_common.base.singleton import SingletonMeta
from icemammoth_common.util.log_util import logger

class FactoryProduction(type):

    def __new__(cls,*args,**kwargs):
        '''
        产生一个新类
        '''
        instance=super().__new__(cls,cls.__name__,args,kwargs)
        cls.__register_model_entity(instance)
        return instance
 
    def __init__(self):
        pass
 
    @classmethod
    def __register_model_entity(cls, instance):
        instanceType = instance.getType()
        if instanceType is None:
            return
        factory = cls.getFactory()
        factory.register(type,instance)

    @classmethod
    def getFactory():
        pass

    def getType(self):
        pass


class Factory(metaclass=SingletonMeta):
    
    '''
    Factory is a singleton class, which is used to register and create production

    工厂模版是一个单例类，用于注册和创建产品, 通过继承该类的方式获得工厂模式能力
    '''

    def __init__(self):
        # 产品类型和产品之间的映射关系
        self.productions: dict = {}

    def register(self, type : any, production: FactoryProduction) -> None:
        '''
        注册产品类型和产品

        参数:
            type: 产品类型
            production: 产品
        '''
        if type not in self.productions:
            logger.info(f'{self.__class__.__module__}.{self.__class__.__name__} register {type}:{production.__class__.__module__}.{production.__class__.__name__}')
            self.productions[type] = production

    def create(self, type: any) -> FactoryProduction | None:
        """生成产品

        Args:
            type (Any): 产品类型

        Returns:
            FactoryProduction | None: 返回产品
        """
        production: any | None = self.productions.get(type)
        logger.info(f'create type {type} production {production}')
        return production

