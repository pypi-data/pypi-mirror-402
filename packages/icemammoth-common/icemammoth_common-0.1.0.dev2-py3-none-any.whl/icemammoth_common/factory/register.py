# -*- coding: utf-8 -*-

import inspect,sys,os,time
from factory import FactoryProduction
from icemammoth_common.util.log_util import logger

def fetchAllModuleNames(module_name):
    module = sys.modules[module_name]
    module_dir = os.path.dirname(module.__file__)
    module_names = []

    for x in os.walk(module_dir):
        x_module_dir = x[0]
        if str.endswith(x_module_dir,'/__pycache__'):
            continue

        relative_dir = x_module_dir[len(module_dir):]
        dir_sub_module = module_name+'.'.join(relative_dir.split('/'))
        module_names.append(dir_sub_module)

        file_names = x[2]
        for file_name in file_names:
            if file_name == '__init__.py' :
                continue
            if not str.endswith(file_name,'.py'):
                continue

            module_names.append(f"{dir_sub_module}.{file_name[:-3]}")

    return module_names

def registerProductionsByModule(module_name):
    if module_name not in sys.modules:
        __import__(module_name, globals(), locals(), [module_name.split('.')[-1]])
    module = sys.modules[module_name]
    members = inspect.getmembers(module)
    classes = []

    productionClasses = set()
    for cls_name, cls_obj in members:
        
        if not inspect.isclass(cls_obj):
            continue
        
        classes.append(cls_name)
        productionClass = getattr(module, cls_name)
        
        if not issubclass(productionClass,FactoryProduction) or productionClass == FactoryProduction:
            continue
        
        productionClasses.add(productionClass)
    
    for productionClass in productionClasses:
        productionClass()

def registerProductionsInModule(module_name):
    start_time = time.time()
    module_names = fetchAllModuleNames(module_name)
    for module_name in module_names:
        # logger.info(f'register factory productions by module {module_name}')
        registerProductionsByModule(module_name)
    end_time = time.time()
    logger.info(f'register factory production cost time:{end_time-start_time}s')