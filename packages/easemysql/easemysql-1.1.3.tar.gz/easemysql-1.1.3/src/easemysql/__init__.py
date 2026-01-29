from .main import EaseMySQL, SQLStatement, SQLSession, SQLSessionContract
from .utils import where_in, where_simple, where_complex
from .ListORM import ListORM

"""
pip install pymysql --upgrade
pip install DBUtils --upgrade

注意1：
select * from test where nickname like "%风行水上%" 
不能直接执行这样的SQL，会提示：not enough arguments for format string
需要使用：cursor.execute('select * from test where nickname like %s', ["%风行水上%"])
原因是：
    pymysql 将字符串中的 % 视为需要格式化的占位符
    占位符：在 pymysql 中，参数化查询的占位符使用 %s，不论数据类型都统一写作 %s
    传入的参数以列表或字典形式提供给 cursor.execute() 方法
"""

VERSION = '1.1.3'

__all__ = [
    "VERSION",
    "EaseMySQL",
    "SQLStatement",
    "SQLSession",
    "SQLSessionContract",
    "where_in",
    "where_simple",
    "where_complex",
    "ListORM",
]
