import pymssql
import pandas as pd


stock_code = '2303,2308,2317,2330,2382,2412,2454,2881,2891,3711'
#stock_code = '2454'
#stock_code = '2891'

def connect_sql_server():
    # you should create a db.py file to save your database settings
    from db import db_settings
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn

def query_stock_data(conn, stock_code):
    # here to change the command to query the stock data
    command = f"""SELECT [date],[o],[h],[l],[c],[v],[K_value],[D_value]
                FROM [dbo].[history_price] 
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

def find_kd_cross(df):
    golden_cross, death_cross = [], []
    for i in range(1, len(df)):
        prev_row = df.iloc[i - 1]
        curr_row = df.iloc[i]
        # prev_row['K'] < 20 and prev_row['D'] < 20 and
        if prev_row['K'] < prev_row['D'] and curr_row['K'] > curr_row['D']:
            golden_cross.append(curr_row.name)
        # prev_row['K'] > 80 and prev_row['D'] > 80 and
        elif prev_row['K'] > prev_row['D'] and curr_row['K'] < curr_row['D']:
            death_cross.append(curr_row.name)  

    return golden_cross, death_cross

# def simulate_martingale_strategy(stock_data):
#     # define the trader
#     holding_share = 0
#     cost = 0
#     cash = 10000000
#     profit = 0
#     last_sell_price = None
#     record = {'holding_share':[], 'cost':[], 'cash':[], 'profit':[]}

#     def update_record():
#         nonlocal holding_share, cost, cash, profit, record
#         for item in ['holding_share', 'cost', 'cash', 'profit']:
#             record[item].append(locals()[item])

#     # define the behavior
#     def buy(row):
#         nonlocal holding_share, cost, cash, buy_dates
#         magnification = 2
#         if holding_share == 0 and cash >= row['Close'] * 1000:
#             holding_share = 1  # start from 1 share or you can change to other number
#             cost += row['Close'] * 1000
#             cash -= cost
#             buy_dates.append(row.name)
            
#         else:
#             if cash < row['Close'] * 1000 * holding_share * magnification:
#                 return
#             cost += row['Close'] * 1000 * holding_share * magnification
#             cash -= row['Close'] * 1000 * holding_share * magnification
#             holding_share += holding_share * magnification
#             buy_dates.append(row.name)

#     def sell(row):
#         nonlocal holding_share, cost, cash, profit, sell_dates, last_sell_price 
#         if holding_share != 0:
#             last_sell_price = row['Close']
#             profit += row['Close'] * 1000 * holding_share - cost
#             cash += row['Close'] * 1000 * holding_share
#             holding_share = 0
#             cost = 0
#             sell_dates.append(row.name)


#     # here to implement the strategy
#     threshold = 0.1
#     buy_times = 0
#     buy_dates, sell_dates = [], []
#     golden_cross, death_cross = find_kd_cross(stock_data)

#     for index, row in stock_data.iterrows():
#         update_record()
#         # if the price is lower than the threshold, buy         --add kd condition
#         if (cost and ((row['Close'] * holding_share * 1000) / cost <= ( 1-threshold ) ) and row.name in golden_cross) or (holding_share == 0 and row.name in golden_cross):
#             if last_sell_price is None or row['Close'] <= last_sell_price * 0.90 or row['Close'] >= last_sell_price * 1.1:
#                 if buy_times == 3:
#                     sell(row)
#                     buy_times = 0
#                     #print('sell',cash)
#                 else:
#                     buy(row)
#                     buy_times += 1
#                     #print('buy',cash)
#         # if the price is higher than the threshold, sell
#         elif (row['Close'] * holding_share * 1000) / (cost+1) >= (1 + 0.3):
#             sell(row)
#             buy_times = 0
#             #print('sell',cash)
#         # if the price is between the threshold, do nothing
#         else:
#             continue
        
#     if holding_share != 0:
#         row = stock_data.iloc[-1]
#         sell(row)
#         update_record()

#     print('cash:', cash)
#     print('profit:', profit)
#     #print('rate of return:',profit/10000000)

#     return record, buy_dates, sell_dates
def simulate_martingale_strategy(stock_data):
    # define the trader
    holding_share = 0
    cost = 0
    cash = 10000000
    profit = 0
    last_sell_price = None
    record = {'holding_share':[], 'cost':[], 'cash':[], 'profit':[]}

    def update_record():
        nonlocal holding_share, cost, cash, profit, record
        for item in ['holding_share', 'cost', 'cash', 'profit']:
            record[item].append(locals()[item])

    # define the behavior
    def buy(row, investment_amount):
        nonlocal holding_share, cost, cash, buy_dates
        shares_to_buy = investment_amount // row['Close']
        if shares_to_buy == 0 or cash < shares_to_buy * row['Close']:
            return
        holding_share += shares_to_buy
        cost += shares_to_buy * row['Close']
        cash -= shares_to_buy * row['Close']
        buy_dates.append(row.name)

    def sell(row):
        nonlocal holding_share, cost, cash, profit, sell_dates, last_sell_price 
        if holding_share != 0:
            last_sell_price = row['Close']
            profit += row['Close'] * holding_share - cost
            cash += row['Close'] * holding_share
            holding_share = 0
            cost = 0
            sell_dates.append(row.name)

    # here to implement the strategy
    threshold = 0.1
    initial_investment = 1000000
    investment_amount = initial_investment
    buy_times = 0
    buy_dates, sell_dates = [], []
    golden_cross, death_cross = find_kd_cross(stock_data)

    for index, row in stock_data.iterrows():
        update_record()
        # if the price is lower than the threshold, buy
        if (cost and ((row['Close'] * holding_share) / cost <= (1 - threshold)) and row.name in golden_cross) or (holding_share == 0 and row.name in golden_cross):
            #if last_sell_price is None or row['Close'] <= last_sell_price * 0.90 or row['Close'] >= last_sell_price * 1.1:
                if buy_times == 3:
                    sell(row)
                    buy_times = 0
                    investment_amount = initial_investment
                else:
                    buy(row, investment_amount)
                    investment_amount *= 2  # double the investment amount each time
                    buy_times += 1
        # if the price is higher than the threshold, sell
        elif ((row['Close'] * holding_share) / (cost + 1) >= (1 + 0.3)) and row.name in death_cross :
            sell(row)
            buy_times = 0
            investment_amount = initial_investment
        # if the price is between the threshold, do nothing
        else:
            continue
        
    if holding_share != 0:
        row = stock_data.iloc[-1]
        sell(row)
        update_record()

    #print('cash:', cash)
    #print('profit:', profit)
    print('rate of return',profit/100000)

    return record, buy_dates, sell_dates

def main():
    try:
        conn = connect_sql_server()
    except Exception as e:
        print(e)
        return
    # query stock data by stock code
    stock_codes = stock_code.split(',')
    for code in stock_codes:
        stock_data = query_stock_data(conn, code)

        # simulate the martingale strategy
        # something output means I am not sure what the output format is ---109502529
        # change somethingoutput to record, buy_dates and sell_dates ---112522023
        print(code)
        record_mar, buy_dates_mar, sell_dates_mar = simulate_martingale_strategy(stock_data)
        # record_gb, buy_date_gb, sell_dates_gb = simulate_gb_strategy(stock_data)
        # calculate cash flow(?) if save in a bank(?)

        # plot the result
        #print_result(stock_data, buy_dates_mar, sell_dates_mar, 'Martinggale')
        # want to add subplot of cost/profit/cash flow under the result, add later :)
        # print_record(record_mar)

    conn.close()



def print_result(df, buy_dates, sell_dates, strategy):
    import mplfinance as mpf
    import numpy as np

    def get_mark(df, buy_dates, sell_dates):
        buy, sell = [], []
        for index, row in df.iterrows():
            if row.name in buy_dates:
                buy.append(row['Close']-10)
            else:
                buy.append(np.nan)
            if row.name in sell_dates:
                sell.append(row['Close']+10)
            else: 
                sell.append(np.nan)
        return buy, sell

    mc = mpf.make_marketcolors(up='r', down='g', edge='', wick='inherit', volume='inherit')
    s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc)
    buy, sell = get_mark(df, buy_dates, sell_dates)
    apds = [
     mpf.make_addplot(buy,type='scatter',markersize=100,marker='^'),
     mpf.make_addplot(sell,type='scatter',markersize=100,marker='v'),
    ]

    fig, axlist = mpf.plot(df,type='candle', style=s,mav=(5,10),volume=True,addplot=apds, returnfig=True)
    newxticks = []
    newlabels = []
    format = '%b-%d'

    # copy and format the existing xticks:
    for xt in axlist[0].get_xticks():
        p = int(xt)
        if p >= 0 and p < len(df):
            ts = df.index[p]
            newxticks.append(p)
            newlabels.append(ts.strftime(format))

    # Here we create the final tick and tick label:
    newxticks.append(len(df)-1)
    newlabels.append(df.index[len(df)-1].strftime(format))

    # set the xticks and labels with the new ticks and labels:
    axlist[0].set_xticks(newxticks)
    axlist[0].set_xticklabels(newlabels)

    # now display the plot:
    mpf.show()

    # save
    fig.savefig(f'Result/{strategy}_{stock_code}.jpg')
    
    print('Result')

# def print_record(record):
    # for item in ['holding_share', 'cost', 'cash', 'profit']:
        
    

if __name__ == '__main__':
    main()
