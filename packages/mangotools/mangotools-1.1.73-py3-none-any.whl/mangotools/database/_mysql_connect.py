# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description:
# @Time   : 2023-09-09 23:17
# @Author : 毛鹏
import pymysql
from pymysql.err import InternalError, OperationalError, ProgrammingError
from pymysql.cursors import DictCursor
from datetime import datetime, date

from ..exceptions import MangoToolsError
from ..exceptions.error_msg import ERROR_MSG_0001, ERROR_MSG_0033, ERROR_MSG_0035, ERROR_MSG_0034
from ..models import MysqlConingModel


class MysqlConnect:

    def __init__(self, mysql_config: MysqlConingModel, is_c: bool = True, is_rud: bool = False):
        self.is_c = is_c
        self.is_rud = is_rud
        self.mysql_config = mysql_config
        self.connection = None
        self._connect()

    def _connect(self):
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.mysql_config.host,
                port=self.mysql_config.port,
                user=self.mysql_config.user,
                password=self.mysql_config.password,
                database=self.mysql_config.database,
                autocommit=True,
                cursorclass=DictCursor,
                charset='utf8mb4',
                connect_timeout=30
            )
        except OperationalError:
            raise MangoToolsError(*ERROR_MSG_0001)
        except InternalError:
            raise MangoToolsError(*ERROR_MSG_0033, value=(self.mysql_config.database,))

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出时自动关闭连接"""
        self.close()

    def __del__(self):
        """析构函数确保连接关闭"""
        self.close()

    def close(self):
        """安全关闭连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                # 忽略关闭时的异常
                pass
            finally:
                self.connection = None

    def _convert_datetime_to_string(self, data):
        """递归将日期时间对象转换为字符串"""
        if isinstance(data, dict):
            return {key: self._convert_datetime_to_string(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_datetime_to_string(item) for item in data]
        elif isinstance(data, (datetime, date)):
            return data.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return data

    def _execute_query(self, cursor, sql):
        """执行查询语句并处理结果"""
        cursor.execute(sql)
        result = cursor.fetchall()

        # 将日期时间转换为字符串
        if result:
            result = self._convert_datetime_to_string(result)

        return result

    def _execute_update(self, cursor, sql):
        """执行更新语句"""
        cursor.execute(sql)
        # autocommit=True 所以不需要手动commit
        return cursor.rowcount

    def condition_execute(self, sql: str) -> list[dict] | list | int | None:
        """条件执行SQL语句"""
        if not sql or not sql.strip():
            return None

        sql_upper = sql.strip().upper()
        is_select = (sql_upper.startswith(('SELECT', 'WITH', 'SHOW', 'DESC', 'DESCRIBE')) or
                     'SELECT' in sql_upper.split(None, 1)[0])

        if is_select:
            if self.is_c:
                return self.execute(sql)
            else:
                return None
        else:
            if self.is_rud:
                return self.execute(sql)
            else:
                return None

    def execute(self, sql: str) -> list[dict] | int | list:
        """执行SQL语句"""
        if not self.connection or not self.connection.open:
            self._connect()

        with self.connection.cursor() as cursor:
            try:
                sql_upper = sql.strip().upper()
                is_select = (sql_upper.startswith(('SELECT', 'WITH', 'SHOW', 'DESC', 'DESCRIBE')) or
                             'SELECT' in sql_upper.split(None, 1)[0])

                if is_select:
                    result = self._execute_query(cursor, sql)
                    return result
                else:
                    result = self._execute_update(cursor, sql)
                    return result

            except ProgrammingError as e:
                raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))
            except InternalError as e:
                raise MangoToolsError(*ERROR_MSG_0035, value=(str(e), ))
            except OperationalError as e:
                if "Lost connection" in str(e) or "MySQL server has gone away" in str(e):
                    try:
                        self._connect()
                        return self.execute(sql)
                    except Exception:
                        raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))
                else:
                    raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))
            except Exception as e:
                raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))
