import pymysql

def connect_sql_server():
    db_setting = {
        "host": "127.0.0.1",
        "user": "",
        "password": "",
        "database": "",
        "charset": "utf8"
    }
    conn = pymysql.connect(**db_setting)
    print('SQL login')
    return conn

def main():
    print('Hello, World!')

def print_result():
    print('Result')

if __name__ == '__main__':
    main()