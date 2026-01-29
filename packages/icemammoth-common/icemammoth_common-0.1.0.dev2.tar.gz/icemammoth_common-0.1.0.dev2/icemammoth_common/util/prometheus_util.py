# -*- coding: utf-8 -*-

import requests
from icemammoth_common.util.log_util import logger
from icemammoth_common.decorator.retry import retry

@retry(tries=3)
def request_data(url='https://thanos-raw.smap.shopee.io/api/v1/query_range', params=None):
    # sourcery skip: raise-specific-error
    if params is None:
        params = {}
    response = requests.get(url, params=params,timeout=(60,120))
    logger.debug('response.status_code = %s',response.status_code)
    if response.status_code != 200:
        try:
            response_json = response.json()
            status = response_json['status']
            error_type = response_json['errorType']
            error = response_json['error']
        except Exception as err:
            logger.exception('query prometheus error!url:%s,params:%s',url,params)
            raise Exception(
                f'unexpected error happend!err:{err},status:{response.status_code},response_text:{response.text}'
            ) from err
        else:
            logger.warning('query prometheus error!url:%s,params:%s,status:%s,error_type:%s,error:%s',url,params,status,error_type,error)
            raise Exception(f'query prometheus error!url:{url},params:{params},status:{status},error_type:{error_type},error:{error}')

    return response.json()