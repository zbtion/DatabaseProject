import pymssql

stock_code = '2330'

def connect_sql_server():
    # you should create a db.py file to save your database settings
    from db import db_settings
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn

def main():
    try:
        conn = connect_sql_server()
    except Exception as e:
        print(e)
        return
    # query stock data by stock code
    # simulate the martingale strategy
    # plot the result

    conn.close()


def print_result():
    print('Result')


if __name__ == '__main__':
    main()
