import re
from typing import Optional, List, Dict
from pymysql.converters import escape_string
from .ListORM import ListORM
from .utils import where_simple
from .session import SQLSessionContract, SQLSession


class SQLStatement:
    _mode_map = {
        'insert': "INSERT INTO",
        'ignore': "INSERT IGNORE INTO",
        # 注意 REPLACE 会把没有传入的字段值置成默认置
        'replace': "REPLACE INTO",
    }

    @classmethod
    def insert(cls, table_name: str, data: dict, mode='insert'):
        fields = []
        values = []
        for k, v in data.items():
            fields.append(f"`{k}`")
            if v is None:
                values.append("NULL")
            else:
                v = escape_string(str(v)).replace("%", "%%")
                values.append(f"'{v}'")
        fields_str = ', '.join(fields)
        values_str = ', '.join(values)

        sql = [cls._mode_map[mode], cls._fmt_dot(table_name), f"({fields_str})", 'VALUES', f"({values_str})"]
        return ' '.join(sql)

    @classmethod
    def insert_all(cls, table_name: str, data: List[Dict], mode='replace'):
        fields_arr = data[0].keys()
        values_arr = []
        for row in data:
            values = []
            for key in fields_arr:
                v = row[key]
                if v is None:
                    values.append('NULL')
                else:
                    values.append("'{}'".format(escape_string(str(v)).replace("%", "%%")))
            values_arr.append(f"({','.join(values)})")
        fields_str = ','.join([f'`{key}`' for key in fields_arr])
        values_str = ','.join(values_arr)

        sql = [cls._mode_map[mode], cls._fmt_dot(table_name), f"({fields_str})", 'VALUES', values_str]
        return ' '.join(sql)

    @classmethod
    def update(cls, table_name, data, condition):
        set_clause = []
        for k, v in data.items():
            if v is None:
                set_clause.append(f"`{k}` = NULL")
            else:
                v = escape_string(str(v)).replace("%", "%%")
                set_clause.append(f"`{k}` = '{v}'")
        set_clause_str = ','.join(set_clause)

        sql = ['UPDATE', cls._fmt_dot(table_name), 'SET', set_clause_str, 'WHERE', condition.replace('?', ' %s ')]
        return ' '.join(sql)

    @classmethod
    def delete(cls, table_name, condition):
        sql = ['DELETE FROM', cls._fmt_dot(table_name), 'WHERE', condition.replace('?', ' %s ')]
        return ' '.join(sql)

    @classmethod
    def select(cls, table_name, condition, field='*'):
        if type(table_name) is str:
            table_name = [table_name, []]
        main_table, join_arr = table_name

        table = cls._fmt_table(main_table)
        for item in join_arr:
            # table2,on,join = ['tabel2','','LEFT JOIN']
            if len(item) == 3:
                table2, on, join = item
            else:
                table2, on = item
                join = 'LEFT JOIN'
            table = f"{table} {join.upper()} {cls._fmt_table(table2)} ON {on}"

        # 书写顺序：SELECT -> FROM -> JOIN -> ON -> WHERE -> GROUP BY -> HAVING -> UNION -> ORDER BY -> LIMIT -> FOR UPDATE
        sql = ['SELECT', field, 'FROM', table, 'WHERE', condition.replace('?', ' %s '), ]
        return ' '.join(sql)

    @classmethod
    def _fmt_dot(cls, dot_str: str):
        arr = dot_str.split('.')
        return '.'.join([f"`{i}`" for i in arr])

    @classmethod
    def _fmt_table(cls, table_str: str):
        # 去除首尾空格并规范化内部空格
        table_str = re.sub(r'\s+', ' ', table_str.strip())

        parts = table_str.split()
        if len(parts) == 2:
            # 格式: table alias
            return f"{cls._fmt_dot(parts[0])} {parts[1]}"
        elif len(parts) == 3 and parts[1].upper() == 'AS':
            # 格式: table as alias
            return f"{cls._fmt_dot(parts[0])} AS {parts[2]}"
        else:
            return table_str


class EaseMySQL:
    def __init__(self, db: Optional[SQLSessionContract] = None, **kwargs):
        self.db = db
        if self.db is None:
            self.db = SQLSession(**kwargs)

        self.last_sql = ''

    def one(self, table_name, condition, params=(), field='*', order=None, group=None, flat=False):
        condition = where_simple(condition)
        if group:
            condition += f' GROUP BY {group}'
        if order:
            condition += f' ORDER BY {order}'
        self.last_sql = SQLStatement.select(table_name, condition, field)
        one = self.db.fetchone(self.last_sql, params)
        if flat and one is not None:
            return list(one.values())[0]
        return one

    def all(self, table_name, condition='1', params=(), field='*', group=None, order=None, limit=None, list_orm=False):
        condition = where_simple(condition)
        if group:
            condition += f' GROUP BY {group}'
        if order:
            condition += f' ORDER BY {order}'
        if limit:
            condition += f' LIMIT {limit}'
        self.last_sql = SQLStatement.select(table_name, condition, field)
        result = self.db.fetchall(self.last_sql, params)
        return ListORM(result) if list_orm else result

    def delete(self, table_name, condition, params=()):
        self.last_sql = SQLStatement.delete(table_name, where_simple(condition))
        _id, cnt = self.db.execute(self.last_sql, params)
        return cnt

    def update(self, table_name, data, condition, params=()):
        self.last_sql = SQLStatement.update(table_name, data, where_simple(condition))
        _id, cnt = self.db.execute(self.last_sql, params)
        return cnt

    def update_many(self, table_name, data, condition, params=()):
        """
        UPDATE chapters
        SET chapter_number = %s,
            chapter_number_prob = %s,
            chapter_title = %s,
            chapter_title_prob = %s,
            processed = 1
        WHERE id = %s

        参数示例
        data:[{'a': 0, 'c': 0}, {'a': 1, 'c': 1},]
        params:[[10], [11],]
        """
        _set = []
        keys = data[0].keys()
        for field in keys:
            _set.append(f"`{field}` = %s")

        _params = []
        for idx, one in enumerate(data):
            row = []
            for field in keys:
                row.append(one[field])
            if len(params) > 0:
                row += params[idx]
            _params.append(tuple(row))

        self.last_sql = ' '.join(['UPDATE', f'`{table_name}`', 'SET', ','.join(_set), 'WHERE', condition])
        _id, cnt = self.db.executemany(self.last_sql, _params)
        return cnt

    def insert(self, table_name, data, params=(), mode=None):
        if not data:
            return None
        if isinstance(data, dict):
            self.last_sql = SQLStatement.insert(table_name, data, mode if mode else 'insert')
            _id, cnt = self.db.execute(self.last_sql, params)
            return _id
        if isinstance(data, list):
            self.last_sql = SQLStatement.insert_all(table_name, data, mode if mode else 'replace')
            _id, cnt = self.db.execute(self.last_sql, params)
            return cnt
        return None

    def raw(self, sql, params=()):
        self.last_sql = sql
        _id, cnt = self.db.execute(sql, params)
        return _id, cnt

    def raw_one(self, sql, params=(), flat=False):
        self.last_sql = sql
        one = self.db.fetchone(sql, params)
        if flat and one is not None:
            return list(one.values())[0]
        return one

    def raw_all(self, sql, params=(), list_orm=False):
        self.last_sql = sql
        result = self.db.fetchall(sql, params)
        return ListORM(result) if list_orm else result


if __name__ == '__main__':
    # python -m src.easemysql.main
    # ValueError: unsupported format character 'A' (0x41) at index 3366
    print(SQLStatement.insert('test', dict(c1=1)))
    print(SQLStatement.insert_all('test', [dict(c1=1, c2=2), dict(c1=1, c2=2)], mode='insert'))
    print(SQLStatement.delete('test', 'id = 1'))
    print(SQLStatement.update('test', dict(c1=55, c2=66), 'id > 0'))
    print(SQLStatement.select('test', 'id > 0'))

    join_tables = [
        ["stat_book_info_show_pv_uv a", "m.zs_id = a.zs_id and a.app_id = 'com.sleepsounds.dztmmd'"],
        ["stat_book_read_progress b", "m.zs_id = b.zs_id", 'left join'],
    ]
    print(SQLStatement.select(['book m', join_tables], 'id > 0'))
