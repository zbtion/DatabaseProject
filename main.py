import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pymssql
import pandas as pd


#stock_code = '3711'

def connect_sql_server():
    # you should create a db.py file to save your database settings
    from db import db_settings
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn


def query_stock_data(conn, stock_code):
    # here to change the command to query the stock data
    command = f"""SELECT [date],[o],[h],[l],[c],[v],[K_value],[D_value]
                FROM [dbo].[stock_price] 
                where [stock_code] = {stock_code} and [date]<='2024-03-08'
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

        if prev_row['K'] < 20 and prev_row['D'] < 20 and prev_row['K'] < prev_row['D'] and curr_row['K'] > curr_row['D'] and curr_row['K'] < 20 and curr_row['D'] < 20:
            golden_cross.append(curr_row.name)
        elif prev_row['K'] > 80 and prev_row['D'] > 80 and prev_row['K'] > prev_row['D'] and curr_row['K'] < curr_row['D'] and curr_row['K'] > 80 and curr_row['D'] > 80:
            death_cross.append(curr_row.name)

    return golden_cross, death_cross


def simulate_martingale_strategy(stock_data, threshold, initial_cash, max_buy_times, initial_holding_share,
                                 magnification):
    # define the trader
    holding_share = 0
    cost = 0
    cash = initial_cash
    profit = 0
    record = {'holding_share': [], 'cost': [], 'cash': [], 'profit': []}
    buy_times = 0

    def update_record():
        nonlocal holding_share, cost, cash, profit, record
        for item in ['holding_share', 'cost', 'cash', 'profit']:
            record[item].append(locals()[item])

    # define the behavior
    def buy(row):
        nonlocal holding_share, cost, cash, buy_dates, buy_times
        #magnification = 5
        if holding_share == 0 and cash >= row['Close'] * 1000:
            holding_share = initial_holding_share  # start from 1 share or you can change to other number
            cost += row['Close'] * 1000 * holding_share
            cash -= cost
            buy_dates.append(row.name)
            print(f"buy at row: {row.name}")

        else:
            if cash < row['Close'] * 1000 * holding_share * magnification:
                return
            cost += row['Close'] * 1000 * holding_share * magnification
            cash -= row['Close'] * 1000 * holding_share * magnification
            holding_share += holding_share * magnification
            buy_dates.append(row.name)
            buy_times += 1
            print(f"buy at row: {row.name}")

    def sell(row):
        nonlocal holding_share, cost, cash, profit, sell_dates, buy_times
        if holding_share != 0:
            profit += row['Close'] * 1000 * holding_share - cost
            cash += row['Close'] * 1000 * holding_share
            holding_share = 0
            cost = 0
            sell_dates.append(row.name)
            buy_times = 0

    # here to implement the strategy

    buy_dates, sell_dates = [], []
    golden_cross, death_cross = find_kd_cross(stock_data)

    for index, row in stock_data.iterrows():
        update_record()
        # if the price is lower than the threshold, buy         --add kd condition  
        if (((cost - row['Close'] * 1000 * holding_share) / (cost + 1) >= threshold) and holding_share != 0) or (
                holding_share == 0 and row.name in golden_cross):
            if buy_times == max_buy_times:
                print(f"before sell at max_buy_time: {row['Close']}, holding_share: {holding_share}, cost: {cost}, max_buy_time: {max_buy_times}, buy_time: {buy_times}")
                sell(row)
            else:
                buy(row)
                
        # if the price is higher than the threshold, sell
        elif (row['Close'] * 1000 * holding_share - cost) / (cost + 1) >= (1 + threshold) and row.name in death_cross:
            print(f"before sell: row[Close]: {row['Close']}, holding_share: {holding_share}, cost: {cost}")
            sell(row)
        # if the price is between the threshold, do nothing
        else:
            continue

    if holding_share != 0:
        row = stock_data.iloc[-1]
        sell(row)
        update_record()

    rate_of_return = profit / initial_cash * 100
    print('cash:', cash)
    print('profit:', profit)

    return record, buy_dates, sell_dates, cash, profit, rate_of_return, golden_cross, death_cross


def main():
    def on_submit():
        try:
            stock_codes = stock_code_entry.get().split(',')
            initial_cash = float(initial_cash_entry.get())
            threshold = float(threshold_entry.get()) / 100
            max_buy_times = int(max_buy_times_entry.get())
            initial_holding_share = int(initial_holding_share_entry.get())
            magnification = int(magnification_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid values.")
            return

        try:
            conn = connect_sql_server()
        except Exception as e:
            print(e)
            return

        for code in stock_codes:
            code = code.strip()
            stock_data = query_stock_data(conn, code)
            print(code)
            record, buy_dates, sell_dates, cash, profit, rate_of_return, golden_cross, death_cross = simulate_martingale_strategy(stock_data,
                                                                                                       threshold,
                                                                                                       initial_cash,
                                                                                                       max_buy_times,
                                                                                                       initial_holding_share,
                                                                                                       magnification)
            print_result(stock_data, buy_dates, sell_dates, 'Martingale_main', code, cash, profit, rate_of_return, golden_cross, death_cross)

        conn.close()
        messagebox.showinfo("Simulation Complete", "The simulation has been completed.")
        root.destroy()

    root = tk.Tk()
    root.title("Martingale Strategy Simulator")

    def validate_float(value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    validate_float_command = root.register(validate_float)

    ttk.Label(root, text="Stock Codes (comma separated)").grid(column=0, row=0, padx=10, pady=5)
    stock_code_entry = ttk.Entry(root, width=50)
    stock_code_entry.grid(column=1, row=0, padx=10, pady=5)

    # 初始現金
    ttk.Label(root, text="Initial Cash").grid(column=0, row=1, padx=10, pady=5)
    initial_cash_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    initial_cash_entry.grid(column=1, row=1, padx=10, pady=5)

    # 閾值
    ttk.Label(root, text="Threshold (%)").grid(column=0, row=2, padx=10, pady=5)
    threshold_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    threshold_entry.grid(column=1, row=2, padx=10, pady=5)

    # 最大購買次數
    ttk.Label(root, text="Max Buy Times").grid(column=0, row=3, padx=10, pady=5)
    max_buy_times_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    max_buy_times_entry.grid(column=1, row=3, padx=10, pady=5)

    # 初始持股數
    ttk.Label(root, text="Initial Holding Share(*1000)").grid(column=0, row=4, padx=10, pady=5)
    initial_holding_share_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    initial_holding_share_entry.grid(column=1, row=4, padx=10, pady=5)

    # 放大倍數
    ttk.Label(root, text="Magnification").grid(column=0, row=5, padx=10, pady=5)
    magnification_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    magnification_entry.grid(column=1, row=5, padx=10, pady=5)

    # 提交按鈕
    submit_button = ttk.Button(root, text="Run Simulation", command=on_submit)
    submit_button.grid(column=0, row=6, columnspan=2, padx=10, pady=20)

    root.mainloop()


def print_result(df, buy_dates, sell_dates, strategy, stock_code, cash, profit, rate_of_return, golden_cross, death_cross):
    import mplfinance as mpf
    import numpy as np

    def get_mark(df, buy_dates, sell_dates):
        buy, sell = [], []
        for index, row in df.iterrows():
            if row.name in buy_dates:
                buy.append(row['Close'] * 0.95)
            else:
                buy.append(np.nan)
            if row.name in sell_dates:
                sell.append(row['Close'] * 1.05)
            else:
                sell.append(np.nan)
        return buy, sell
    
    def get_mark_cross(df, golden_cross, death_cross):
        golden_marks, death_marks = [], []
        for index, row in df.iterrows():
            if row.name in golden_cross:
                golden_marks.append(row['D'])
            else:
                golden_marks.append(np.nan)
            if row.name in death_cross:
                death_marks.append(row['D'])
            else:
                death_marks.append(np.nan)
        return golden_marks, death_marks


    mc = mpf.make_marketcolors(up='r', down='g', edge='', wick='inherit', volume='inherit')
    s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc)
    buy, sell = get_mark(df, buy_dates, sell_dates)
    golden_marks, death_marks = get_mark_cross(df, golden_cross, death_cross)
    apds = [
        mpf.make_addplot(buy, type='scatter', markersize=100, marker='^'),
        mpf.make_addplot(sell, type='scatter', markersize=100, marker='v'),
        mpf.make_addplot(df['K'], panel=1, color='orange', secondary_y=True, alpha=0.5, ylim=(0, 100)),
        mpf.make_addplot(df['D'], panel=1, color='blue', secondary_y=True, alpha=0.5, ylim=(0, 100)),
        mpf.make_addplot(golden_marks, type='scatter', panel=1, color='orange', marker='o', markersize=50, ylim=(0, 100)),
        mpf.make_addplot(death_marks, type='scatter', panel=1, color='blue', marker='o', markersize=50, ylim=(0, 100))
    ]

    fig, axlist = mpf.plot(df, type='candle', style=s, mav=(5, 10), volume=False, addplot=apds, returnfig=True)
    axlist[0].text(0.02, 0.95, f'Cash: {cash:.2f}', transform=axlist[0].transAxes, fontsize=12, verticalalignment='top')
    axlist[0].text(0.02, 0.90, f'Profit: {profit:.2f}', transform=axlist[0].transAxes, fontsize=12,
                   verticalalignment='top')
    axlist[0].text(0.02, 0.85, f'Rate of Return: {rate_of_return:.2f}%', transform=axlist[0].transAxes, fontsize=12,
                   verticalalignment='top')
    axlist[2].set_ylabel('KD Value')
    
    newxticks = []
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
    newxticks.append(len(df) - 1)
    newlabels.append(df.index[len(df) - 1].strftime(format))

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