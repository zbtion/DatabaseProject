import pymssql
import pandas as pd
import numpy as np


stock_code = '2330'

def connect_sql_server():
    # you should create a db.py file to save your database settings
    from db import db_settings
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn

'''
query_stock_data function(Record)
    109502529 2024/06/04 add query_stock_data function
    ...(please add the record, if you have modified the function)
'''
def query_stock_data(conn, stock_code):
    # here to change the command to query the stock data
    command = f"""SELECT [date],[o],[h],[l],[c],[v],[K_value],[D_value]
                FROM [dbo].[stock_data] 
                where [stock_code] = {stock_code}
                order by [date] asc"""
    cursor = conn.cursor()
    cursor.execute(command)
    
    arr = []
    for row in cursor:
        arr.append(row)
    
    df = pd.DataFrame(arr)
    df['Date'] = pd.to_datetime(df[0])
    df = df.drop(columns=[0])
    df.set_index('Date', inplace=True)

    # if you change the command, you should check the column name
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'K', 'D']
    
    #print(df.head())

    return df

def simulate_martingale_strategy(stock_data):
    # todo: implement the martingale strategy
    pass

def main():
    try:
        conn = connect_sql_server()
    except Exception as e:
        print(e)
        return
    # query stock data by stock code
    stock_data = query_stock_data(conn, stock_code)

    # simulate the martingale strategy
    # something output means I am not sure what the output format is ---109502529
    something_output = simulate_martingale_strategy(stock_data)
    
    # plot the result
    print_result(something_output)

    conn.close()


def print_result(something):
    print('Result')


if __name__ == '__main__':
    main()
