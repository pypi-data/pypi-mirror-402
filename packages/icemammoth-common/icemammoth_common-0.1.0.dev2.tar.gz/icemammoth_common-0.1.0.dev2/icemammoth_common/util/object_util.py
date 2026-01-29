# -*- coding: utf-8 -*-

from typing import List
from icemammoth_common.util.log_util import logger


def fetchObjectAttributes(obj) -> List[str]:
    return [
        attribute
        for attribute in dir(obj)
        if not attribute.startswith("__") and not callable(getattr(obj, attribute))
    ]
    
def existAttribute(obj, attrName):
    return attrName in fetchObjectAttributes(obj)

def getObjectAttributesAndValues(obj):
    attributes = [
        attribute
        for attribute in dir(obj)
        if not attribute.startswith("__") and not callable(getattr(obj, attribute))
    ]
    return {attribute: getattr(obj, attribute) for attribute in attributes}

def attrsLessThan(*valuePairs):
    for valuePair in valuePairs:
        if valuePair[0] == valuePair[1]:
            continue
        if valuePair[0] is None:
            return True
        return False if valuePair[1] is None else valuePair[0] < valuePair[1]
    return True


def shallowCopyAttribute(source, dest):
    sourceAttrValuesMap = getObjectAttributesAndValues(source)
    attributes = [
        attribute
        for attribute in dir(dest)
        if not attribute.startswith("__") and not callable(getattr(dest, attribute))
    ]
    for attribute in attributes:
        if sourceValue := sourceAttrValuesMap.get(attribute):
            setattr(dest,attribute,sourceValue)
