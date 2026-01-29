# 以下是添加中文注释后的完整代码
import importlib.util
import sys

def module_exist(module_name:str) -> bool:
    '''判断模块是否存在'''
    return importlib.util.find_spec(module_name) is not None

def get_variable(module_name:str, variable_name:str, default_value:object = None, except_unexist :bool = False) -> object | None:
    '''获取模块中的变量'''
    module = sys.modules.get(module_name)
    if module is None:
        if except_unexist:
            raise ValueError(f"Module '{module_name}' does not exist")
        else:
            return default_value
        
    if hasattr(module, variable_name):
        return getattr(module,variable_name)
    elif except_unexist:
        raise AttributeError(f"Variable '{variable_name}' not found in module '{module_name}'")
    else:
        return default_value

def has_variable(module_name:str, variable_name:str) -> bool:
    '''判断模块中是否存在变量'''
    module = sys.modules.get(module_name)
    return module is not None and hasattr(module, variable_name)