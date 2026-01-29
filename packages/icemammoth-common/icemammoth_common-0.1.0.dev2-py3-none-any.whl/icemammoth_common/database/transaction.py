# -*- coding: utf-8 -*-

import threading
from decorator import decorator
from icemammoth_common.util.log_util import logger
from icemammoth_common.database.connect_pool import ConnectPool

'''
    ThreadLocal.local每次调用都会返回一个新对象,并非线程内唯一
    作为全局变量方便实现线程的内变量共享,放到函数体内则在函数每次执行时会生成不同的变量,无法实现线程的内变量共享
    这点与Java中的ThreadLocal相同
'''
local = threading.local()

class TransactionManager(object):
    
    connection = None
    inTransaction = False
    
    def __init__(self):
        self.connectionPool = ConnectPool()
    
    def startTx(self):
        TransactionManager.connection = self.connectionPool.getConnection()
        TransactionManager.connection.start_transaction()
        TransactionManager.inTransaction = True
    
    def commit(self):
        try:
            TransactionManager.connection.commit()
            TransactionManager.connection.close()
        finally:
            TransactionManager.connection = None
            TransactionManager.inTransaction = False
    
    def rollback(self):
        try:
            TransactionManager.connection.rollback()
            TransactionManager.connection.close()
        finally:
            TransactionManager.connection = None
            TransactionManager.inTransaction = False
            
def transaction():
    @decorator
    def transaction_decorator(f, *fargs, **fkwargs):
        firstLevel = False
        # transactionManager = None
        try:
            local.transactionManager
        except AttributeError as error:
            logger.debug('no transactionManager in thread local')
            logger.debug('enter transaction scope')
            local.transactionManager = None

        if not local.transactionManager:
            firstLevel = True
            local.transactionManager = TransactionManager()
            # transactionManager = local.transactionManager
        
        try:
            if firstLevel:
                logger.debug(msg='start transaction')
                local.transactionManager.startTx()
            result = f(*fargs,**fkwargs)
            if firstLevel:
                logger.debug('commit transaction')
                local.transactionManager.commit()
            return result
        except Exception as exception:
            if firstLevel and local.transactionManager.inTransaction:
                logger.exception(f'transaction execute failed, rollback!func:{f.__module__}:{f.__qualname__}')
                local.transactionManager.rollback()
            raise exception
        finally:
            if firstLevel:
                logger.debug('exit transaction scope')
                local.transactionManager = None
        
    return transaction_decorator