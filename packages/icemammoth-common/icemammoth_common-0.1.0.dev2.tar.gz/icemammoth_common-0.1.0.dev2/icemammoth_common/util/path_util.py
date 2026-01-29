# -*- coding: utf-8 -*-

from os import path

"""
    path中生成最终路径的函数有realpath(),abspath()和normpath()
    realpath(): 返回canonical path, 对于链接还原为真实目录,函数实现依赖abspath()
    abspath():  返回absolute path,  函数实现依赖,normpath()
    normpath(): 返回normalization path, 表示常用的目录表达方式,去除双斜杠,相对路径等,其路径中可能包含链接
    
    Canonical path: 规范路径,将路径中的link转化为所连接的真实路径
                    The canonical path is always an absolute and unique path
    Absolute path:  绝对路径,路径中包含从根目录到达该目录或文件的所有目录和文件信息,不进行link转换
                    An absolute path is defined as the specifying the location 
                    of a file or directory from the root directory(/). 
                    In other words we can say absolute path is a complete path 
                    from start of actual filesystem from / directory.
    Normalization path: 标准路径,去除双斜杠,单点,双点等相对路径符号,不要求从根目录开始,可以包含link
                    Normalize a path, e.g. A//B, A/./B and A/foo/../B all become A/B.
                    It should be understood that this may change the meaning of the path
                    if it contains symbolic links!
"""

def create_real_path(*paths):
    return path.realpath(path.join(*paths))

def create_abs_path(*paths):
    return path.abspath(path.join(*paths))

def create_norm_path(*paths):
    return path.norm(path.join(*paths))