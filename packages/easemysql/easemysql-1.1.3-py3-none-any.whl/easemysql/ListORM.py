class LookupResolve:
    def __init__(self, lookup):
        self.lookup = lookup

    def match(self, value, query):
        lookup = self.lookup.lower()
        if lookup == 'in':
            return value in query
        if lookup == 'contains':
            return query in f"{value}"
        return True

    @classmethod
    def and_match(cls, item: dict, **kwargs):
        match = True
        for key, value in kwargs.items():
            if '__' in key:
                key, lookup = f"{key}".split('__')
                if not cls(lookup).match(item.get(key), value):
                    match = False
                    break
            else:
                if item.get(key) != value:
                    match = False
                    break
        return match

    @classmethod
    def or_match(cls, item: dict, *args):
        if not args:
            return True
        match = []
        for where_dic in args:
            match.append(cls.and_match(item, **where_dic))
        return any(match)


class ListORM:
    def __init__(self, data_list: list):
        self._data = data_list

    def __iter__(self):
        for item in self._data:
            yield item

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"<ListORM object at {id(self)}>===={str(self._data)}===="

    def filter(self, *args, **kwargs):
        result = []
        for item in self._data:
            match = all([
                LookupResolve.or_match(item, *args),
                LookupResolve.and_match(item, **kwargs),
            ])
            if match:
                result.append(item)
        return ListORM(result)

    def group_by(self, *args, **kwargs):
        groups = dict()
        for item in self._data:
            key = tuple([item[field] for field in args])
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        result = []
        for keys, items in groups.items():
            _dic = dict(zip(args, keys))
            if field := kwargs.get('sum'):
                _dic[f"sum({field})"] = sum([i[field] for i in items])

            if field := kwargs.get('count'):
                _dic[f"count({field})"] = len(items)

            result.append(_dic)
        return ListORM(result)

    def order_by(self, *args):
        def _sort_key(row):
            arr = []
            for field in args:
                reverse = False
                if field.startswith('-'):
                    reverse = True  # reverse True 为倒序
                    field = field[1:]
                value = row[field]
                if isinstance(value, str) and len(value) > 0:
                    value = ord(value[0])
                if isinstance(value, (int, float)):
                    value = -value if reverse else value
                arr.append(value)

            return tuple(arr)

        self._data.sort(key=lambda x: _sort_key(x))
        return self

    def count(self):
        return len(self._data)

    def get(self) -> list:
        return self._data

    def get_map(self, *args):
        _map = dict()
        for item in self._data:
            if len(args) > 1:
                k = '@'.join([str(item[_]) for _ in args])
            else:
                k = item[args[0]]
            _map[k] = item
        return _map

    def first(self):
        if not self._data:
            return None
        return self._data[0]

    def sum(self, field):
        return sum([item[field] for item in self._data])

    def values_list(self, field, flat=True):
        arr = field.replace(' ', '').split(',')
        result = []
        for item in self._data:
            if flat:
                result.append(item[arr[0]])
            else:
                result.append([item[field] for field in arr])
        return result


if '__main__' == __name__:
    data = [
        {"hosp_id": 86, "p1": 'aa', "p2": 1, "p3": 3},
        {"hosp_id": 87, "p1": 'aa', "p2": 1, "p3": 8},
        {"hosp_id": 89, "p1": 'bb', "p2": 2, "p3": 5},
        {"hosp_id": 88, "p1": 'bb', "p2": 2, "p3": 1},
    ]

    orm = ListORM(data)
    # print(orm.filter(hosp_id=86).count())
    # print(orm.filter(hosp_id__in=[86, 87]).order_by('p3').get())
    # print(orm.filter(hosp_id__in=[86, 87]).sum('p3'))
    # print(orm.filter(hosp_id=86).first())
    # print(orm.filter().values_list('p1', flat=True))
    # for i in orm:
    #     print(i)
    #
    # print(orm.get_map('hosp_id'))
    # print(orm.values_list('hosp_id'))
    # print(len(orm))
    #
    # print('=' * 10)
    arr = orm.filter().order_by('p1', '-p3').get()
    for i in arr:
        print(i)

    print(orm.group_by('p2', sum='p3'))
