# -*- coding: utf-8 -*-

from mysql.connector import pooling
from icemammoth_common.util import module_util
from icemammoth_common.base.singleton import SingletonMeta
from icemammoth_common.util import module_util
from icemammoth_common.util import log_util

CONFIG_MODULE_NAME = "config"

class ConnectPool(metaclass=SingletonMeta):

    def __init__(self):

        if not module_util.module_exist(CONFIG_MODULE_NAME):
            log_util.logger.exception(
                "config module is not exist, must set config module first!")
            raise Exception(
                "config module is not exist, must set config module first!")

        datebase_host = module_util.get_variable(
            CONFIG_MODULE_NAME, "DATABASE_HOST", except_unexist=True)
        database_port = module_util.get_variable(
            CONFIG_MODULE_NAME, "DATABASE_PORT", except_unexist=True)
        database_user = module_util.get_variable(
            CONFIG_MODULE_NAME, "DATABASE_USER", except_unexist=True)
        database_password = module_util.get_variable(
            CONFIG_MODULE_NAME, "DATABASE_PASSWORD", except_unexist=True)
        database_db_name = module_util.get_variable(
            CONFIG_MODULE_NAME, "DATABASE_DB_NAME", except_unexist=True)
        database_connect_pool_size = module_util.get_variable(
            CONFIG_MODULE_NAME, "DATABASE_CONNECT_POOL_SIZE", except_unexist=True)

        # dbconfig = {
        #     "host": datebase_host,
        #     "port": database_port,
        #     "user": database_user,
        #     "password": database_password,
        #     "database":database_db_name,
        # }

        self.cnxpool = pooling.MySQLConnectionPool(host=datebase_host,
                                                   port=database_port,
                                                   user=database_user,
                                                   password=database_password,
                                                   database=database_db_name,
                                                   pool_name="connection-pool",
                                                   pool_reset_session=True,
                                                   pool_size=database_connect_pool_size,
                                                   autocommit=True)

    def getConnection(self):
        return self.cnxpool.get_connection()
