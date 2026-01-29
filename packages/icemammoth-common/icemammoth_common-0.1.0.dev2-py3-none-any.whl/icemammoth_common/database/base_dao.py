# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Tuple, TypeVar, Generic
from icemammoth_common.base import BaseObject

from icemammoth_common.database.connect_pool import ConnectPool
from icemammoth_common.error.error import NotExistError
from .transaction import TransactionManager
from icemammoth_common.util.log_util import logger
from icemammoth_common.util import string_util, object_util

class ModelAttrValueConvertor(object):

    def attrValueToColumnValue(self, table, attrName, attrValue):
        pass

    def columnValueToAttrValue(self, table, columnName, columnValue):
        pass


class DAOInheritException(BaseException):

    def __init__(self, msg):
        super(msg)


class ORMConfig(BaseObject):

    def __init__(
        self,
        table: str = None,
        # columns: [str] = None,
        model=None,
        columnAttrMap: Dict[str, str] = None,
        attrValueConvertor: ModelAttrValueConvertor = None,
    ):
        self.table = table
        self.model = model
        self.columnAttrMap = columnAttrMap
        self.attrValueConvertor = attrValueConvertor


# 使用泛型,必须先使用TypeVar定义泛型类型
ModelType = TypeVar("ModelType", bound=BaseObject)

def defaultProcessFunc(cursor) :
    return cursor.fetchall()


class BaseDAO(Generic[ModelType]):

    def __init__(self):
        if not self.__ORM_CONFIG__:
            raise DAOInheritException(
                f"class {
                    self.__class__.__name__} inherit from BaseDAO must set attribute __ORM_CONFIG__"
            )
        self.ormConfig = self.__ORM_CONFIG__
        self.table = self.ormConfig.table
        self.modelType = self.ormConfig.model
        self.modelAttrs = object_util.fetchObjectAttributes(self.ormConfig.model())
        self.attrColumnMap = {}
        self.columnAttrMap = {}
        self.mappedColumns = []
        self.mappedAttrs:List[str] = []
        for column, attr in self.ormConfig.columnAttrMap.items():
            if not attr:
                attr = string_util.underscore_to_camel(column)
            if attr not in self.modelAttrs:
                raise NotExistError(
                    f"dao {self.__class__.__name__} orm config error, class {self.ormConfig.model.__name__} doesn't exist attribute {
                        attr} which is mapped with column {self.table}.{column}"
                )
            self.attrColumnMap[attr] = column
            self.columnAttrMap[column] = attr
            self.mappedColumns.append(column)
            self.mappedAttrs.append(attr)

        self.attrValueConvertor = self.ormConfig.attrValueConvertor
        self.connectionPool = ConnectPool()
        self.transactionManager = TransactionManager()

    def _fetchValuesByAttrs(self, model, attrs=None) -> List[Any]:
        row = []

        attrValueMap = object_util.getObjectAttributesAndValues(model)
        attrs = attrs if attrs else self.mappedAttrs

        for attr in attrs:
            value = attrValueMap.get(attr)
            value = self.attrValueConvertor.attrValueToColumnValue(
                self.table, attr, value) if self.attrValueConvertor else value
            row.append(value)

        return row
    def fillRowDataToModel(self, columns: List[str], row: List[Any], model):

        if row is None or columns is None:
            return None

        for idx, column in enumerate(columns):
            attr = self._fetchAttrByColum(column)
            if not attr:
                raise NotExistError(
                    f"dao {self.__class__.__name__} convert row to model failed, class {
                        self.ormConfig.model.__name__} no attribute mapped with column {self.table}.{column}."
                )
            value = row[idx]
            value = self.attrValueConvertor.columnValueToAttrValue(
                self.table, column, value) if self.attrValueConvertor else value
            setattr(model, attr, value)
        return model

    def _insertData(self, cursor):
        return cursor.lastrowid

    def _insertDatas(self, cursor):
        return (cursor.lastrowid, cursor.rowcount)

    def _readDatas(self, cursor):
        return (
            [
                self.fillRowDataToModel(
                    cursor.column_names, result, self.ormConfig.model())
                for result in results
            ]
            if (results := cursor.fetchall())
            else None
        )

    def _readData(self, cursor):
        result = cursor.fetchone()
        return self.fillRowDataToModel(cursor.column_names, result, self.ormConfig.model())

    def _deleteDatas(self, cursor):
        return cursor.rowcount

    def _updateDatas(self, cursor):
        return cursor.rowcount

    def execute(self, sql: str, params:List[Any], process_func=None, executeMany=False):
        try:
            connection = None
            if self.transactionManager.inTransaction:
                connection = self.transactionManager.connection
            else:
                connection = self.connectionPool.getConnection()
            cursor = connection.cursor()
            if executeMany:
                cursor.executemany(sql, params)
            else:
                cursor.execute(sql, params)
        
            result = None
            if process_func is None:
                result = defaultProcessFunc(cursor)
            else:
                result = process_func(cursor)
            cursor.close
            return result
        except Exception as e:
            logger.exception(
                f"execute sql failed!sql:{sql},params:{params},executeMany:{executeMany}"
            )
            raise e
        finally:
            if not self.transactionManager.inTransaction and connection:
                connection.close()

    def insertData(self, model: ModelType, ignoreDuplicate=False, duplicateUpdateAttrs: List[str] = [], duplicateUpdateTerms: List[str] = []) -> int:
        sql: str = self._generateInsertSql(ignoreDuplicate=ignoreDuplicate, duplicateUpdateAttrs=duplicateUpdateAttrs, duplicateUpdateTerms=duplicateUpdateTerms)
        logger.debug(f"sql is {sql}")
        params: List[Any] = self._fetchValuesByAttrs(model)
        return self.execute(sql, params, self._insertData)

    def insertDatas(self, models: List[ModelType], ignoreDuplicate=False, duplicateUpdateAttrs: List[str] = [], duplicateUpdateTerms: List[str] = []) -> Tuple[int]:
        sql: str = self._generateInsertSql(ignoreDuplicate=ignoreDuplicate, duplicateUpdateAttrs=duplicateUpdateAttrs, duplicateUpdateTerms=duplicateUpdateTerms)
        logger.debug(f"sql is {sql}")
        params: List[List[Any]] = [self._fetchValuesByAttrs(model) for model in models]
        return self.execute(sql, params, self._insertDatas, True)

    def insertDatasByBatch(self, models: List[ModelType], ignoreDuplicate=False, duplicateUpdateAttrs: List[str] = [], duplicateUpdateTerms: List[str] = [], pageSize:int=1000) -> Tuple[int,int]:
        sql: str = self._generateInsertSql(ignoreDuplicate=ignoreDuplicate, duplicateUpdateAttrs=duplicateUpdateAttrs, duplicateUpdateTerms=duplicateUpdateTerms)
        logger.debug(f"sql is {sql}")
        result: Tuple[int,int] = [0, 0]
        start: int = 0
        while start < len(models):
            end: int = min(start + pageSize, len(models))
            _models: List[Any] = models[start:end]
            params: List[List[Any]] = [self._fetchValuesByAttrs(model) for model in _models]
            _result = self.execute(sql, params, self._insertDatas, True)
            result = [x + y for x, y in zip(result, _result)]
            start = end
        
        return result
    def _generateInsertSql(self, insertAttrs: List[str] = None, ignoreDuplicate=False, duplicateUpdateAttrs: List[str] = [], duplicateUpdateTerms: List[str] = []):
        columns = []
        if insertAttrs:
            for attr in insertAttrs:
                column = self._fetchColumnByAttr(attr)
                columns.append(column)
        else:
            columns = self.mappedColumns
        columnsSQL = ",".join(columns)
        ignoreDuplicateTag = 'IGNORE' if ignoreDuplicate else ''
        valuesSQL = ','.join(['%s']*len(columns))

        duplicateUpdateSQL: str = ""
        if not ignoreDuplicate:
            
            if duplicateUpdateAttrs:

                duplicateUpdateSQL = 'ON DUPLICATE KEY UPDATE'
                for attr in duplicateUpdateAttrs:
                    column = self._fetchColumnByAttr(attr)
                    duplicateUpdateSQL = f'{duplicateUpdateSQL} {column} = VALUES({column}), '

            if duplicateUpdateTerms:
                for term in duplicateUpdateTerms:
                    duplicateUpdateSQL = f'{duplicateUpdateSQL} {term}, '

            if duplicateUpdateSQL[-2:] == ', ':
                duplicateUpdateSQL = duplicateUpdateSQL[:-2]

        return f"INSERT {ignoreDuplicateTag} INTO {self.table} ({columnsSQL}) VALUES ({valuesSQL}) {duplicateUpdateSQL}"

    def readData(self, readAttrs: List[str] = None, **conditions) -> ModelType:
        sql = self._generateReadSql(
            readOne=True, readAttrs=readAttrs, **conditions)
        params = list(conditions.values())
        return self.execute(sql, params, self._readData)

    def readDatas(self, readAttrs: List[str] = None, **conditions) -> List[ModelType]:
        sql = self._generateReadSql(
            readOne=False, readAttrs=readAttrs, **conditions)
        params = list(conditions.values())
        return self.execute(sql, params, self._readDatas)

    def readDatasByConditionSQL(
        self, readAttrs: List[str] = None, conditionSql: str = None, params = None, orderBy:str = None, limit:int = None, offset:int = None
    ) -> List[ModelType]:

        # 定义一个空列表，用于存储要读取的列
        readColumns = []
        # 如果readAttrs不为空，则遍历readAttrs，将每个属性对应的列添加到readColumns中
        if readAttrs:
            for attr in readAttrs:
                column = self._fetchColumnByAttr(attr)
                readColumns.append(column)
        # 如果readAttrs为空，则将mappedColumns赋值给readColumns
        else:
            readColumns = self.mappedColumns
        columnsSQL: str = ",".join(readColumns)

        selectSQL = f"SELECT {columnsSQL} FROM {self.table}"
        
        if conditionSql:
            selectSQL = f"{selectSQL} WHERE {conditionSql}"
        
        if orderBy:
            selectSQL = f"{selectSQL} ORDER BY {orderBy}"

        if limit:
            selectSQL = f"{selectSQL} LIMIT {limit}"

        if offset:
            selectSQL = f"{selectSQL} OFFSET {offset}"
        
        return self.execute(selectSQL, params, self._readDatas)

    def _generateReadSql(self, readOne: bool = False, readAttrs: List[str] = None, **conditions):

        params = []

        readColumns = []
        if readAttrs:
            for attr in readAttrs:
                column = self._fetchColumnByAttr(attr)
                readColumns.append(column)
        else:
            readColumns = self.mappedColumns
        columnsSQL: str = ",".join(readColumns)

        conditionColumns = []
        for attr, value in conditions.items():
            column = self._fetchColumnByAttr(attr)
            conditionColumns.append(column)
            value = self.attrValueConvertor.attrValueToColumnValue(
                self.table, attr, value) if self.attrValueConvertor else value
            params.append(value)
        conditionSQL: str = " and ".join(
            [f"{column} = %s" for column in conditionColumns])

        limitSQL: str = "LIMIT 1" if readOne else ""

        return f"SELECT {columnsSQL} FROM {self.table} WHERE {conditionSQL} {limitSQL}"

    def deleteDatas(self, **conditions):

        params = []

        conditionColumns = []
        for attr, value in conditions.items():
            column = self._fetchColumnByAttr(attr)
            conditionColumns.append(column)
            value = self.attrValueConvertor.attrValueToColumnValue(
                self.table, attr, value) if self.attrValueConvertor else value
            params.append(value)
        conditionSQL = " AND ".join(
            [f"{column} = %s" for column in conditionColumns])

        deleteSQL = f"DELETE FROM {self.table} WHERE {conditionSQL}"

        return self.execute(deleteSQL, params, self._deleteDatas)

    def updateDatas(self, updateAttrs: Dict[str, str], **conditions):

        updateColumns = []
        params = []

        for attr, value in updateAttrs.items():
            column = self._fetchColumnByAttr(attr)
            updateColumns.append(column)
            columnValue = self.attrValueConvertor.attrValueToColumnValue(
                self.table, attr, value) if self.attrValueConvertor else value
            params.append(columnValue)
        updateColumnSQL = ', '.join(
            [f'{column} = %s' for column in updateColumns])

        conditionColumns = []
        for attr, value in conditions.items():
            column = self._fetchColumnByAttr(attr)
            conditionColumns.append(column)
            columnValue = self.attrValueConvertor.attrValueToColumnValue(
                self.table, attr, value) if self.attrValueConvertor else value
            params.append(columnValue)
        conditionSQL = " AND ".join(
            [f"{column} = %s" for column in conditionColumns])

        updateSQL = f"UPDATE {self.table} SET {
            updateColumnSQL} WHERE {conditionSQL}"

        return self.execute(updateSQL, params, self._updateDatas)

    def _fetchColumnByAttr(self, attr: str):
        column = self.attrColumnMap.get(attr)
        if not column:
            raise TypeError(f'table {self.table} not column bind with attr {
                            self.modelType.__qualname__}.{attr}')
        return column

    def _fetchAttrByColum(self, column):
        attr = self.columnAttrMap.get(column)
        if not attr:
            raise TypeError(f'{self.modelType.__qualname__} not attribute bind with table {
                            self.table} column {column}')
        return attr