from .config import *
import psycopg2


def select(table, value='*', filter_by=None, count=1):
    request = f'select {value} from {table.__tablename__}'
    filters = filter_by
    if filters:
        request += ' where '
        for index, fil in enumerate(filters):
            if index > 1:
                request += f'and {fil}={filters[fil]} '
            else:
                request += f'{fil}={filters[fil]} '
    else:
        request += ';'

    try:
        with psycopg2.connect(
                host=host,
                port=port,
                user=user,
                database=db_name,
                password=password,
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(request + ';')

                if count >= 0:
                    results = cursor.fetchmany(count)
                elif count == -1:
                    results = cursor.fetchall()

                attrsintable = [i for i in table.__dict__ if not '__' in i]
                attrs = {}
                objects = []
                for result in results:
                    for index, attr in enumerate(attrsintable):
                        attrs[attr] = result[index]
                    obj = table()
                    obj.__dict__.update(attrs)
                    objects.append(obj)

                return objects

    except Exception as _e:
        raise _e


def insert(table_obj):
    request = f'insert into {table_obj.__tablename__} ('
    attrs = [i for i in table_obj.__dict__ if '__' not in i]
    for index, attr in enumerate(attrs):
        value = getattr(table_obj, attr)
        if hasattr(value, 'autoincrement'):
            if not value.autoincrement:
                request += f'{attr}' + (', ' if not index + 1 == len(attrs) else '')
        else:
            request += f'{attr}' + (', ' if not index + 1 == len(attrs) else '')

    request += ') values ('
    for index, attr in enumerate(attrs):
        value = getattr(table_obj, attr)
        if hasattr(value, 'autoincrement'):
            if not value.autoincrement:
                request += repr(value) + (', ' if not index + 1 == len(attrs) else ');')
        else:
            request += repr(value) + (', ' if not index + 1 == len(attrs) else ');')

    try:
        with psycopg2.connect(
                host=host,
                port=port,
                user=user,
                database=db_name,
                password=password,
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(request)
            return True

    except Exception as _e:
        print('error', _e)
        return False


def update(table, **kwargs):
    request = f'update {table.__tablename__} set '
    values = kwargs['values']
    for index, value in enumerate(values):
        request += f'{value}={repr(values[value])} ' + (', ' if index + 1 != len(values) else 'where ')

    where_s = kwargs['where']
    for index, where in enumerate(where_s):
        request += f'{where}={repr(where_s[where])} ' + (', ' if index + 1 != len(where_s) else ';')

    try:
        with psycopg2.connect(
                host=host,
                port=port,
                user=user,
                database=db_name,
                password=password,
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(request)
            return True

    except Exception as _e:
        print('error', _e)
        return False


def delete(table, **kwargs):
    request = f'delete from {table.__tablename__} where '
    where_s = kwargs['where']
    for index, where in enumerate(where_s):
        request += f'{where}={repr(where_s[where])} ' + ('and ' if index + 1 != len(where_s) else ';')

    try:
        with psycopg2.connect(
                host=host,
                port=port,
                user=user,
                database=db_name,
                password=password,
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(request)
            return True
    except Exception as _e:
        print('error', _e)
        return False
