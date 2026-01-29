import os,io
from pathlib import Path
from icemammoth_common.util.log_util import logger

class DefaultDirFilesProcessor(object):
    
    def processDir(self, dir,subDir):
        print(f'Processing directory dir:{dir},sub_dir:{subDir}')
    
    def processFile(self, dir,file):
        print(f'Processing line dir:{dir},file:{file}')

def loop_dir(dir, dirProcessFunc=None, fileProcessFunc=None, recursive=True):

    for root, dirs, files in os.walk(dir, topdown=True):
            
        if dirProcessFunc:
            for subDir in dirs:
                dirProcessFunc(root,subDir)
                if recursive:
                    loop_dir(os.path.join(root,subDir), dirProcessFunc, fileProcessFunc)
        if fileProcessFunc:
            for file in files:
                fileProcessFunc(root,file)

class CleanDirProcessor(object):
    
    def processDir(self, dir,subDir):
        os.rmdir(os.path.join(dir, subDir))
    
    def processFile(self, dir,file):
        os.remove(os.path.join(dir, file))

'''
    清理目录
    create_not_exist:目录不存在时是否创建
'''
def clean_dir(dir, create_not_exist=True):
    dir: str = rf"{dir}"
    if not os.path.exists(dir):
        if create_not_exist:
            logger.info(f"[INFO] not exist directory {dir}, create it.")
            os.makedirs(dir)
        return
    loop_dir(dir,CleanDirProcessor())

'''
    如果目录不存在创建目录
'''
def create_dir_if_not_exist(dir):
    dir: str = rf"{dir}"
    if not os.path.exists(dir):
        logger.info(f"[INFO] not exist directory {dir}, create it.")
        try:
            os.makedirs(dir)
        except FileExistsError:
            return
        except Exception as e:
                raise e


'''
    清理目录
    create_not_exist:目录不存在时是否创建
'''
def reset_dir(dir,create_not_exist=True):
    clean_dir(dir,create_not_exist)
    
'''
    删除文件
    create_not_exist:当文件目录不存在时是否创建
'''
def remove_file(file, create_dir_not_exist=True):
    # sourcery skip: avoid-builtin-shadow
    dir = os.path.dirname(file)
    if not os.path.exists(dir):
        if create_dir_not_exist:
            os.makedirs(dir,exist_ok=True)
    elif os.path.exists(file):
        os.remove(file)

'''
    将内容写入文件
'''
def dumpToFile(path,content):
    remove_file(path,True)
    with open(path,'w') as file:
        file.write(content)
        file.flush()

class DefaultFileReadProcessor(object):
    
    def processLine(self, filePath, index, line):
        logger.info(f'Processing file:{filePath}, index:{index},line:{line[:16]}')


class FileContentReadProcessor(object):


    def __init__(self) -> None:
        self.content = ""
    
    def processLine(self, filePath, index, line):
        logger.info('process line: %s' % line)
        self.content = self.content + line +'\n'

    def getContent(self):
        return self.content

'''
    读取文件,并对其内容进行处理
    processor:文件数据处理类
'''
def readFile(filepath, processor=DefaultFileReadProcessor()):
    # sourcery skip: raise-specific-error
    
    with io.open(filepath, 'r') as file:
        index = 0
        try:
            lines: list[str] = file.readlines()
            for line in lines:
                logger.debug('Read line: %s' % line)
                if line.endswith("\n"):
                    line = line[:-1]
                processor.processLine(filepath, index, line)
                index += 1
        except Exception as err:
            logger.exception(f'read and process file error! file:{filepath},processor:{type(processor)}')

            raise Exception(
                f'read and process file error! file:{filepath},processor:{type(processor)}'
            ) from err
        
def saveMapData(filePath, mapData):
    content = ''
    for k,v in mapData.items():
        line = f'{k}:{v}'
        content = content + line + '\n'
    dumpToFile(filePath, content)

# -*- coding: utf-8 -*-

class MapDataReader(object):

    def __init__(self):
        self.mapData = {}
    
    def processLine(self, filePath, index, line):
        firstColonIndex = line.find(':')
        if firstColonIndex > -1:
            sline = line.strip()
            key = sline[:firstColonIndex]
            value = sline[firstColonIndex+1:]
            self.mapData[key] = value
        
    def getMapData(self):
        return self.mapData
    
def loadMapData(filepath, exception_on_file_noexist=True):
    if not exception_on_file_noexist and not os.path.exists(filepath):
        return {}
        
    mapDataReader = MapDataReader()
    readFile(filepath, processor=mapDataReader)
    return mapDataReader.getMapData()

'''
    将内容写入文件
'''
def dumpBytesToFile(path,contentBytes):
    remove_file(path,True)
    with open(path,'wb') as file:
        # file.write(BytesIO(contentBytes).getbuffer())
        # file.flush()
        file.write(contentBytes)

def appendToFile(path,content) -> None:
    with open(path,'a') as file:
        file.write(content)

'''
    读取文件内容,并对其内容进行处理
    processor:文件数据处理类
'''
def readFileCotent(filepath :str, processor=DefaultFileReadProcessor()) -> str:
    
    processor = FileContentReadProcessor()
    readFile(filepath, processor)
    return processor.getContent()

'''
    获取文件扩展名
'''
def fetchFileExtension(file):
    fullpath = Path(file)
    return fullpath.suffix

'''
    获取文件名不包含扩展名
'''
def fetchFileNameWithoutExtension(file):
    fullpath = Path(file)
    return fullpath.stem

'''
    获取文件名包含扩展名
'''
def fetchFileNameWithExtension(file):
    fullpath = Path(file)
    return fullpath.name