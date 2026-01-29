# EaseMySQL

一个简单易用的MySQL封装库，帮助开发者更高效地处理MySQL数据库操作。

## 主要功能

- 数据库连接池管理
- 简化的CRUD操作接口
- SQL语句构建辅助函数
- 支持参数化查询，防止SQL注入
- 单例模式确保每个连接配置只创建一个连接池

## 安装方法

pip install --upgrade easemysql -i https://pypi.org/simple/

> 依赖的库
```
pip install pymysql --upgrade
pip install DBUtils --upgrade
```

## 快速开始

```python
from easemysql import EaseMySQL

# 配置数据库连接
config = dict(host='localhost', user='username', password='password', database='dbname')
db = EaseMySQL(**config)

# 查询单条记录
result = db.one('table_name', dict(id=1))

# 查询多条记录
results = db.all('table_name', 'status = ?', [1])

# 使用条件列表进行复杂查询
results = db.all('table_name', [
    'or',
    ['in', 'id', [1, 3, 4]],
    ['and', ['>', 'id', 5], 'id < 8', dict(id=[6, 7])],
    dict(id=8),
    dict(id=[9]),
])

# 插入记录
db.insert('table_name', dict(name='test', value=123))

# 更新记录
db.update('table_name', dict(value=456), 'id = 1')

# 删除记录
db.delete('table_name', 'id = 1')
```