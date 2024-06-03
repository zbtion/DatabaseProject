import pymssql


def connect_sql_server():
    db_settings = {
        "host": "127.0.0.1",
        'user': 'add365',
        'password': '1234',
        'database': 'ncu_database',
        'charset': 'utf8'
    }
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
