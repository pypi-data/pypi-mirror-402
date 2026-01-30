# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: MySQL 连接池，支持多线程环境
# @Time   : 2024-01-04 10:00
# @Author : 毛鹏
import threading
import time
from queue import Queue, Empty, Full
from typing import Optional, Any
from datetime import datetime, date

import pymysql
from pymysql.err import InternalError, OperationalError, ProgrammingError
from pymysql.cursors import DictCursor

from ..exceptions import MangoToolsError
from ..exceptions.error_msg import ERROR_MSG_0001, ERROR_MSG_0033, ERROR_MSG_0035, ERROR_MSG_0034
from ..models import MysqlConingModel


class MysqlConnectionPool:
    """MySQL 连接池类，支持多线程环境"""

    def __init__(
        self,
        mysql_config: MysqlConingModel,
        pool_size: int = 10,
        max_overflow: int = 20,
        timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_delay: float = 0.5,
        is_c: bool = True,
        is_rud: bool = False
    ):
        """
        初始化连接池

        Args:
            mysql_config: MySQL 配置
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            timeout: 获取连接超时时间(秒)
            retry_attempts: 重试次数
            retry_delay: 重试延迟(秒)
            is_c: 是否允许查询操作
            is_rud: 是否允许增删改操作
        """
        self.mysql_config = mysql_config
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.is_c = is_c
        self.is_rud = is_rud

        # 连接池状态
        self._pool: Queue = Queue(maxsize=pool_size)
        self._overflow_connections = set()
        self._overflow_count = 0
        self._created_connections = 0

        # 线程同步
        self._lock = threading.RLock()
        self._overflow_lock = threading.Lock()

        # 初始化连接池
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn)
                self._created_connections += 1
            except Exception as e:
                # 如果连接失败，继续创建其他连接
                continue

        if self._created_connections == 0:
            raise MangoToolsError(*ERROR_MSG_0001)

    def _create_connection(self):
        """创建新的数据库连接"""
        try:
            connection = pymysql.connect(
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
            return connection
        except OperationalError:
            raise MangoToolsError(*ERROR_MSG_0001)
        except InternalError:
            raise MangoToolsError(*ERROR_MSG_0033, value=(self.mysql_config.database,))

    def get_connection(self):
        """获取连接"""
        with self._lock:
            try:
                # 首先尝试从池中获取连接
                connection = self._pool.get(timeout=self.timeout)
                if self._is_connection_valid(connection):
                    return connection
                else:
                    # 连接无效，关闭并创建新连接
                    connection.close()
                    return self._create_connection()
            except Empty:
                # 池为空，尝试创建溢出连接
                return self._create_overflow_connection()

    def _create_overflow_connection(self):
        """创建溢出连接"""
        with self._overflow_lock:
            if self._overflow_count >= self.max_overflow:
                raise MangoToolsError("连接池已满，无法创建更多连接")

            try:
                connection = self._create_connection()
                self._overflow_connections.add(connection)
                self._overflow_count += 1
                return connection
            except Exception:
                raise MangoToolsError("无法创建溢出连接")

    def put_connection(self, connection):
        """归还连接到池中"""
        if connection is None:
            return

        with self._lock:
            try:
                if connection in self._overflow_connections:
                    # 这是溢出连接
                    with self._overflow_lock:
                        self._overflow_connections.remove(connection)
                        self._overflow_count -= 1
                    connection.close()
                else:
                    # 这是池连接
                    if self._is_connection_valid(connection):
                        try:
                            self._pool.put(connection, timeout=1.0)
                        except Full:
                            # 池已满，关闭连接
                            connection.close()
                    else:
                        # 连接无效，关闭并创建新连接
                        connection.close()
                        try:
                            new_conn = self._create_connection()
                            self._pool.put(new_conn, timeout=1.0)
                        except Full:
                            new_conn.close()
            except Exception:
                # 确保连接被关闭
                try:
                    connection.close()
                except Exception:
                    pass

    def _is_connection_valid(self, connection):
        """检查连接是否有效"""
        if not connection or not connection.open:
            return False

        try:
            # 执行简单查询检查连接
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            # 关闭池中的连接
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except Exception:
                    pass

            # 关闭溢出连接
            with self._overflow_lock:
                for conn in self._overflow_connections.copy():
                    try:
                        conn.close()
                    except Exception:
                        pass
                self._overflow_connections.clear()
                self._overflow_count = 0

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_all()

    def __del__(self):
        """析构函数"""
        self.close_all()

    def get_pool_status(self):
        """获取连接池状态"""
        with self._lock:
            with self._overflow_lock:
                return {
                    'pool_size': self.pool_size,
                    'created_connections': self._created_connections,
                    'available_connections': self._pool.qsize(),
                    'overflow_connections': self._overflow_count,
                    'total_connections': self._pool.qsize() + self._overflow_count
                }


class MysqlPoolConnect:
    """基于连接池的 MySQL 连接类，参照 MysqlConnect 设计"""

    def __init__(self, mysql_config: MysqlConingModel, pool_size: int = 10,
                 max_overflow: int = 20, is_c: bool = True, is_rud: bool = False):
        """
        初始化连接池连接类

        Args:
            mysql_config: MySQL 配置
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
            is_c: 是否允许查询操作
            is_rud: 是否允许增删改操作
        """
        self.mysql_config = mysql_config
        self.is_c = is_c
        self.is_rud = is_rud

        # 创建连接池
        self.pool = MysqlConnectionPool(
            mysql_config=mysql_config,
            pool_size=pool_size,
            max_overflow=max_overflow,
            is_c=is_c,
            is_rud=is_rud
        )

        self._local = threading.local()

    def __enter__(self):
        """支持上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出时归还连接"""
        self.close()

    def __del__(self):
        """析构函数"""
        self.close()
        self.pool.close_all()

    def close(self):
        """归还连接到池中"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self.pool.put_connection(self._local.connection)
            self._local.connection = None

    def _get_connection(self):
        """获取线程本地连接"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = self.pool.get_connection()
        return self._local.connection

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
        connection = self._get_connection()
        max_retries = self.pool.retry_attempts
        retry_delay = self.pool.retry_delay

        for attempt in range(max_retries):
            try:
                with connection.cursor() as cursor:
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
                    if attempt < max_retries - 1:
                        # 重新获取连接
                        self.close()
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))
                else:
                    raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise MangoToolsError(*ERROR_MSG_0034, value=(sql, str(e)))

    def get_pool_status(self):
        """获取连接池状态"""
        return self.pool.get_pool_status()
