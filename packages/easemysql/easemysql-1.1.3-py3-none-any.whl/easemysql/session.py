import time
import threading
import pymysql
import warnings
from abc import ABC, abstractmethod
from dbutils.pooled_db import PooledDB

warnings.filterwarnings('ignore', category=pymysql.Warning)
lock = threading.Lock()


class SQLSessionContract(ABC):
    @abstractmethod
    def execute(self, sql, args=None):
        pass

    @abstractmethod
    def executemany(self, sql, args=None):
        pass

    @abstractmethod
    def fetchone(self, sql, args=None):
        pass

    @abstractmethod
    def fetchall(self, sql, args=None):
        pass


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        key = '@'.join(str(_) for _ in kwargs.values())
        with lock:
            if key not in instances:
                instances[key] = cls(*args, **kwargs)
        return instances[key]

    return get_instance


@singleton
class SQLSession(SQLSessionContract):
    # SQLSession(host='', user='', password='', database='')
    def __init__(self, **kwargs):
        conf = kwargs
        t1 = time.time()
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=conf.get('maxconnections', 10),  # 允许的最大连接数，超过时新请求将会等待连接被释放
            mincached=conf.get('mincached', 1),  # 启动时的初始连接数
            maxcached=conf.get('maxcached', 10),  # 最大空闲连接数量，超出的连接将会被关闭
            blocking=conf.get('blocking', True),  # 当连接数达到 maxconnections 并且没有空闲连接可用时，是否等待连接被释放。否则将抛出异常
            cursorclass=pymysql.cursors.DictCursor,  # 设置查询结果为字典
            # conv={
            #     pymysql.converters.FIELD_TYPE.DATETIME: str
            # },
            use_unicode=True,
            host=conf['host'],
            port=conf.get('port', 3306),
            user=conf['user'],
            password=conf['password'],
            database=conf['database']
        )
        self.log = ['{} 初始化连接，用时：{}'.format(time.time(), time.time() - t1)]
        self.execute_cnt = 0

    def __connection(self):
        # 如果你不调用 conn.close()，连接会保持开放状态，直到 PooledDB 的连接池自行处理（即回收或重用）这些连接。
        # 由于你使用了连接池，不调用 conn.close() 也不会导致资源泄漏，连接池会管理连接的生命周期。
        return self.pool.connection()

    def __cursor_execute(self, conn, cursor, sql, args):
        self.execute_cnt += 1
        try:
            cursor.execute(sql, args)
        except Exception as e:
            conn.rollback()
            # print(e)
            # print(sql)
            # print(args)
            # exit()
            raise Exception('{e} \n SLQ:{sql}; \n args:{args}'.format(e=e, sql=sql, args=args))

    def execute(self, sql, args=None):
        conn = self.__connection()
        with conn.cursor() as cursor:
            self.__cursor_execute(conn, cursor, sql, args)
            cnt = cursor.rowcount
            _id = cursor.lastrowid
        conn.commit()
        return _id, cnt

    def executemany(self, sql, args=None):
        conn = self.__connection()
        with conn.cursor() as cursor:
            self.execute_cnt += 1
            cursor.executemany(sql, args)
            cnt = cursor.rowcount
            _id = cursor.lastrowid
        conn.commit()
        return _id, cnt

    def fetchone(self, sql, args=None):
        conn = self.__connection()
        with conn.cursor() as cursor:
            self.__cursor_execute(conn, cursor, sql, args)
            result = cursor.fetchone()
        return result

    def fetchall(self, sql, args=None):
        conn = self.__connection()
        with conn.cursor() as cursor:
            self.__cursor_execute(conn, cursor, sql, args)
            result = cursor.fetchall()
        return result
