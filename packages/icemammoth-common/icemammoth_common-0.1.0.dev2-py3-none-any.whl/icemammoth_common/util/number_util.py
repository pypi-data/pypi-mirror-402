# -*- coding: utf-8 -*-

import math
from icemammoth_common.util.log_util import logger

def str_to_float(s,default = None):
    if s is None:
        return default
    try:
        if type(s) == str:
            s = s.strip().replace(',','')
        return float(s)
    except ValueError:
        logger.warning(f'{s} is illegal float, return None')
        return None
    
def str_to_int(s):
    if s is None:
        return None
    
    try:
        return int(s.strip().replace(',',''))
    except ValueError:
        logger.warning(f'{s} is illegal int, return None')
        return None
    
def base26_to_decimal(s):
    s = s.upper()
    num = 0
    for i in s:
        num = num * 26 + ord(i) - ord('A')
    return num
    
def decimal_to_base26(num):
    s = ''
    while num > 0:
        s = chr(num % 26 + ord('A')) + s
        num //= 26
    return s

def convertByPrecision(f:float, precision:int) -> float:
    return round(f,precision) if precision >= 0 else math.trunc(f/math.pow(10,-precision)) * math.pow(10,-precision)

def roundToInt(number) -> int:
    if type(number) == float:
        return int(round(number,1))
    elif type(number) == int:
        return number
    elif type(number) == str:
        return int(round(float(number),1))
    else:
        raise TypeError(f'number is not valid type converting to int!number:{number},type:{type(number)}')
    
def calculate_pages(total_items, pagesize):
    pages = (total_items + pagesize - 1) // pagesize
    return pages