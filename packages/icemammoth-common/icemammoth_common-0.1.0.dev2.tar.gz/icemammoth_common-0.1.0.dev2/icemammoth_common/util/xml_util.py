# -*- coding: utf-8 -*-

import inspect
import xml.etree.ElementTree as ET
from util import object_util


class DefaultTagGenerator:
    
    def generateTag(self,tag):
        return tag[0].upper() + tag[1:]
        
    def generateListMemberTag(self,listTag):
        return 'Item'
    
def convertObjToXMLElement(obj, eleTag, parentTag=None, tagGenerator=DefaultTagGenerator()):
    
    if eleTag is None:
        raise ValueError("eleTag can not be None!")

    generatedEleTag = tagGenerator.generateTag(eleTag)
    if parentTag is not None:
        generatedGarentTag = tagGenerator.generateTag(parentTag)
        ele = ET.Element(generatedGarentTag)
        subEle = convertObjToXMLElement(obj,generatedEleTag,tagGenerator=tagGenerator)
        ele.append(subEle)
        return ele
    
    ele = ET.Element(generatedEleTag)
    if isinstance(obj,str):
        ele.text = obj
    elif isinstance(obj,list) or isinstance(obj,tuple) or isinstance(obj, set) or isinstance(obj, frozenset):
        listMemberTag = tagGenerator.generateListMemberTag(eleTag)
        for v in obj:
            subEle = convertObjToXMLElement(v, listMemberTag,tagGenerator=tagGenerator)
            ele.append(subEle)
    elif isinstance(obj,int) or isinstance(obj,float) or isinstance(obj,complex) or \
        isinstance(obj, bool) or isinstance(obj, bytes) or isinstance(obj, bytearray):
        ele.text = str(obj)
    elif isinstance(obj, dict):
        for k,v in obj.items():
            subEle = convertObjToXMLElement(v,k,tagGenerator=tagGenerator)
            ele.append(subEle)
    elif inspect.isclass(obj.__class__):
        for k,v in object_util.getObjectAttributesAndValues(obj).items():
            subEle = convertObjToXMLElement(v,k,tagGenerator=tagGenerator)
            ele.append(subEle)
    else:
        raise ValueError(f'unkown data type {type(obj)}')

    return ele

def convertObjToXMLString(obj, eleTag, parentTag=None, tagGenerator=DefaultTagGenerator()):

    ele = convertObjToXMLElement(obj,eleTag,parentTag,tagGenerator)
    ET.indent(ele, space='  ', level=0)
    return str(ET.tostring(ele,encoding='unicode',method='xml'))