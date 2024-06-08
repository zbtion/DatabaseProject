import pymssql
import pandas as pd


stock_code = '2330'

def connect_sql_server():
    # you should create a db.py file to save your database settings
    from db import db_settings
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn


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
    # define the trader
    holding_share = 0
    cost = 0
    cash = 1000000
    profit = 0

    # define the behavior
    def buy(row):
        nonlocal holding_share, cost, cash
        magnification = 2
        if holding_share == 0:
            holding_share = 1  # start from 1 share or you can change to other number
            cost += row['Close'] * 1000
            cash -= cost
        else:
            cost += row['Close'] * 1000 * holding_share * magnification
            cash -= row['Close'] * 1000 * holding_share * magnification
            holding_share += holding_share * magnification

    def sell(row):
        nonlocal holding_share, cost, cash, profit
        if holding_share != 0:
            profit += row['Close'] * 1000 * holding_share - cost
            cash += row['Close'] * 1000 * holding_share
            holding_share = 0
            cost = 0

    # here to implement the strategy
    threshold = 0.1
    buy_times = 0
    something_output = None

    for index, row in stock_data.iterrows():
        # if the price is lower than the threshold, buy
        if (cost - row['Close'] * holding_share) / cost >= threshold or holding_share == 0:
            if buy_times == 3:
                sell(row)
                buy_times = 0
            else:
                buy(row)
                buy_times += 1
        # if the price is higher than the threshold, sell
        elif (row['Close'] * holding_share - cost) / cost >= threshold:
            sell(row)
        # if the price is between the threshold, do nothing
        else:
            continue
    
    if holding_share != 0:
        row = stock_data.iloc[-1]
        sell(row)

    print('cash:', cash)
    print('profit:', profit)

    return something_output

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
