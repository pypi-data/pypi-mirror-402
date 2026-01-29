# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict
import coloredlogs
import sys

from icemammoth_common.util import module_util

CONFIG_MODULE_NAME = "config"

log_level: int = logging.INFO

logger: logging.Logger = logging.getLogger(__name__)

# color类型
# colors:{'black','blue','cyan','green','magenta','red','white','yellow'}

# 字符样式
# text_styles:{'bold','bright','faint','inverse','normal','strike_through','underline'}

# 定义日志字段样式的字典
field_style: Dict[str, Any] = {'asctime': {'color': 'green'},  # 时间戳字段样式，使用绿色文本
                               # 日志级别字段样式，使用加粗的黑色文本
                               'levelname': {'bold': True, 'color': 'black'},
                               'filename': {'color': 'cyan'},  # 文件名字段样式，使用青色文本
                               'funcName': {'color': 'blue'},  # 函数名字段样式，使用蓝色文本
                               }

# 定义不同日志级别样式的字典
level_styles: Dict[str, Any] = {'critical': {'bold': True, 'color': 'red'},  # 致命错误级别样式，使用加粗的红色文本
                                'debug': {'color': 'green'},  # 调试级别样式，使用绿色文本
                                'error': {'color': 'red'},  # 错误级别样式，使用红色文本
                                'info': {'color': 'cyan'},  # 信息级别样式，使用青色文本
                                # 警告级别样式，使用黄色文本
                                'warning': {'color': 'yellow'},
                                }
"""
此函数调用`coloredlogs.install()`来配置并激活一个带有颜色的日志记录器。
日志格式如下：

- 时间戳: %(asctime)s
- 级别: [%(levelname)s]
- 文件名: %(filename)s
- 函数名: %(funcName)s
- 行号: %(lineno)s
- 消息: %(message)s

日志时间戳格式化为 '%Y-%m-%d %H:%M:%S'。

此外，还可以通过`field_styles`和`level_styles`参数定制字段和级别样式。

@params:
- level: 日志级别，例如 logging.DEBUG, logging.INFO 等。
- logger: 要配置的日志器实例。
- fmt: 定制的日志消息格式字符串。
- datefmt: 时间戳的自定义日期时间格式。
- field_styles: 字段样式的字典，用于指定颜色和其他样式。
- level_styles: 级别样式的字典，用于指定不同日志级别颜色和其他样式。

@example:
coloredlogs.install(level=logging.INFO, logger=my_logger, ...)
"""
coloredlogs.install(level=log_level,
                    logger=logger,
                    fmt='%(asctime)s [%(levelname)s] [%(filename)s:%(funcName)s:%(lineno)s] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    field_styles=field_style,
                    level_styles=level_styles)


if CONFIG_MODULE_NAME not in sys.modules:
    # 如果模块没有加载，则 warning日志级别
    logger.warning(f"[Log Boot Info] not found config module! set default log config!")
elif not module_util.has_variable(CONFIG_MODULE_NAME, 'LOG_LEVEL') and not module_util.has_variable(CONFIG_MODULE_NAME, 'LOG_LEVEL'):
    # 如果没有，则 warning日志级别
    logger.warning("[Log Boot Info] LOG_LEVEL/log_level not set in {config_module} module! set default log config!")
else:
    # 获取LOG_LEVEL的值
    log_level = module_util.get_variable(CONFIG_MODULE_NAME, 'LOG_LEVEL')
    if not log_level:
        # 如果没有，则获取log_level的值
        log_level = module_util.get_variable(CONFIG_MODULE_NAME, 'log_level')

# 打印日志启动信息
logger.info(f"[Log Boot Info] set log level: {logging.getLevelName(log_level)}.")
# 设置日志级别
logger.setLevel(log_level)


# 重新调整设置日志级别
coloredlogs.adjust_level(logger, level=log_level)
