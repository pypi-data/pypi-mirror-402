# -*- coding: utf-8 -*-

from typing import Any, Tuple
import requests
from enum import Enum
from requests import Response
from requests.structures import CaseInsensitiveDict
from icemammoth_common.util.log_util import logger
from icemammoth_common.decorator.retry import retry

class ResponseType(Enum):
    TEXT = 'TEXT'
    JSON = 'JSON'
    BYTES = 'BYTES'

DEFAULT_HEADER: dict[str, str] = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh-CN;q=0.7,zh;q=0.6',
        'content-type': 'application/json',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    }

def post(url, headers:dict[str,str]=DEFAULT_HEADER, data = None, responseType:ResponseType = ResponseType.TEXT) -> Tuple[int, CaseInsensitiveDict[str], Any]:
    return send_http_request(url, 'post', headers = headers, data = data, responseType = responseType)

def get(url, headers:dict[str,str]=DEFAULT_HEADER, params:dict[str,str] = None, responseType:ResponseType = ResponseType.TEXT) -> Tuple[int, CaseInsensitiveDict[str], Any]:
    return send_http_request(url, 'get' , headers = headers, params = params, responseType = responseType)

def handle_exception(exception):
    if type(exception) == FileNotFoundError:
        return True
    return False

@retry(tries=3,on_exception=handle_exception)
def send_http_request(url, method:str='GET', **kwargs) -> Tuple[int, CaseInsensitiveDict[str], Any]:
    '''
        responseType can be:
            TEXT(default): return response context as a string 
            JSON: return response context as a json
            BYTES: return response context as byte array
    '''
    legalMethods: tuple = ('GET', 'POST')
    if not method or method.upper() not in legalMethods:
        raise TypeError(f'requestType type {method} is not one of legal requestType types {legalMethods}')
    responseType = kwargs.pop('responseType')
    if not responseType or type(responseType) is not ResponseType:
        raise TypeError(f'param responseType must not be none and type must be ResponseType!responseType:{responseType}')
    try:
        logger.debug(f'request url={url},method=,{method},{kwargs}')
        kwargs.setdefault('timeout',(60, 120))
        response: Response = requests.request(method.lower(), url, **kwargs)

        statusCode: int = response.status_code
        header: CaseInsensitiveDict[str] = response.headers

        # 409 Conflict: conflict with the current state of the target resource. 
        if int(statusCode/100) == 5 or statusCode in [403,409]:
            logger.exception(f'http request filed!url:{url},method:{method},{kwargs},responseCode:{response}, failedReason:{response.reason}')
            raise Exception(response)
                
        # Unauthorized
        if statusCode == 401:
            logger.exception(f'http request unauthorized!url:{url},method:{method},{kwargs},responseCode:{response}, failedReason:{response.reason}')
            raise Exception(response)

        # Resource Not Found
        if statusCode == 404:
            logger.exception(f'http request not found file!url:{url},method:{method},{kwargs},responseCode:{response}, failedReason:{response.reason}')
            raise FileNotFoundError(response)
            
        if responseType == ResponseType.TEXT:
            return statusCode,header,response.text
        elif responseType == ResponseType.JSON:
            return statusCode,header,response.json()
        elif responseType == ResponseType.BYTES:
            return statusCode,header,response.content
        else:
            raise TypeError(f'param responseType must not be none and type must be ResponseType!responseType:{responseType}')
    except Exception as err:
        logger.exception(f'send http request error!url:{url},method:{method},{kwargs}')
        raise err