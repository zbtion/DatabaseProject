import pymssql
from db import db_settings


def connect_sql_server():
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn


def main():
    try:
        conn = connect_sql_server()
    except Exception as e:
        print(e)
    print('Hello, World!')


def print_result():
    print('Result')


if __name__ == '__main__':
    main()
