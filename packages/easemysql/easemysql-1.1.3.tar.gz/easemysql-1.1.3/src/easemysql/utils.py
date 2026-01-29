from typing import Optional, List, Dict
import re


def is_safe_field_name(field_name: str) -> bool:
    if not field_name:
        return False

    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', field_name):
        return False

    # 检查SQL关键字（部分常见的）
    sql_keywords = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'TRUNCATE', 'UNION', 'EXEC', 'EXECUTE'
    }
    if field_name.upper() in sql_keywords:
        return False

    return True


def _supported_sql_operators(condition: list) -> tuple[str, list]:
    operators = {
        'OR': 1,
        'AND': 1,
        'IN': 1,
        'NOT IN': 1,
        'BETWEEN': 1,
        '=': 1,
        '>': 1,
        '<': 1,
        '>=': 1,
        '<=': 1,
    }
    first = condition[0]
    if type(first) is str:
        first = first.upper()
        if first in operators:
            return first, condition[1:]
    return 'AND', condition[:]


def where_in(ids):
    if isinstance(ids, list):
        _str = ''
        for _id in ids:
            if isinstance(_id, (int, float)):
                _str += "{},".format(_id)
            else:
                _str += "'{}',".format(_id)
        return _str[:-1]
    return ids


def where_simple(condition) -> str:
    if isinstance(condition, str):
        return condition

    if isinstance(condition, list):
        return where_complex(condition)

    if isinstance(condition, dict):
        _arr = []
        for k, v in condition.items():
            if type(v) is list:
                _arr.append(f"{k} IN ({where_in(v)})")
            else:
                if isinstance(v, (int, float)):
                    _arr.append(f"{k} = {v}")
                else:
                    _arr.append(f"{k} = '{v}'")
        return ' AND '.join(_arr)

    raise Exception('Unsupported parameter type')


def where_complex(condition) -> str:
    """
    [
        'OR',
        [
            'AND',
            {'is_open': 1},
            'is_safe >= 10',
            ['>=', 'id', 100]
        ],
        ['IN', 'device_id', [1, 2, 3]]
    ]
    :return:
    """
    if not isinstance(condition, list):
        return '({})'.format(where_simple(condition))

    operator, values = _supported_sql_operators(condition)

    if operator in ['=', '>', '<', '>=', '<=']:
        return '({} {} {})'.format(values[0], operator, values[1])
    if operator in ['BETWEEN']:
        return '({} {} {} AND {})'.format(values[0], operator, values[1], values[2])
    if operator in ['IN', 'NOT IN']:
        return '({} {} ({}))'.format(values[0], operator, where_in(values[1]))
    # or, and
    return '({})'.format(f" {operator} ".join([where_complex(_) for _ in values]))


if '__main__' == __name__:
    print(where_simple('id > 0'))
    print(where_simple(dict(a=1, b=2, c=[1, 2, 3])))
    print(where_simple(['BETWEEN', 'id', 1, 100]))
    print(where_simple(['IN', 'id', [1, 100]]))
    print(where_simple(['IN', 'id', ['1', '100']]))
    print(where_simple(['in', 'id', '1,2,3']))
