import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pymssql
import pandas as pd
stock_code = '2303,2308,2317,2330,2382,2412,2454,2881,2891,3711'
def connect_sql_server():
    from db import db_settings
    conn = pymssql.connect(**db_settings)
    print('SQL login')
    return conn

def query_stock_data(conn, stock_code):
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
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'K', 'D']

    return df

def find_kd_cross(df):
    golden_cross, death_cross = [], []
    for i in range(1, len(df)):
        prev_row = df.iloc[i - 1]
        curr_row = df.iloc[i]
        if prev_row['K'] < 20 and prev_row['D'] < 20 and prev_row['K'] < prev_row['D'] and curr_row['K'] > curr_row['D']:
            golden_cross.append(curr_row.name)
        elif prev_row['K'] > 80 and prev_row['D'] > 80 and prev_row['K'] > prev_row['D'] and curr_row['K'] < curr_row['D']:
            death_cross.append(curr_row.name)  

    return golden_cross, death_cross

def simulate_martingale_strategy(stock_data, threshold, initial_investment, initail_cash, max_buy_times, use_trailing_stop, trailing_stop_percent, stop_profit_percent, buy_multiplier):
    holding_share = 0
    cash = initail_cash
    cost = 0
    profit = 0
    record = {'holding_share':[], 'cost':[], 'cash':[], 'profit':[]}

    def update_record():
        nonlocal holding_share, cost, cash, profit, record
        for item in ['holding_share', 'cost', 'cash', 'profit']:
            record[item].append(locals()[item])

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
        nonlocal holding_share, cost, cash, profit, sell_dates
        if holding_share != 0:
            profit += row['Close'] * holding_share - cost
            cash += row['Close'] * holding_share
            holding_share = 0
            cost = 0
            sell_dates.append(row.name)

    investment_amount = initial_investment
    buy_times = 0
    buy_dates, sell_dates = [], []
    golden_cross, death_cross = find_kd_cross(stock_data)

    monitor_levels = [stop_profit_percent + i * 0.1 for i in range(int((2 - stop_profit_percent) / 0.1) + 1)]
    max_profit_level = 0
    
    for index, row in stock_data.iterrows():
        update_record()
        if (((row['Close'] * holding_share) / (cost+1) <= (1 - threshold))) or (holding_share == 0 and row.name in golden_cross):
            if buy_times == max_buy_times:
                sell(row)
                buy_times = 0
                investment_amount = initial_investment
                max_price = 0
            else:
                buy(row, investment_amount)
                investment_amount *= buy_multiplier
                buy_times += 1
                max_price = row['Close']
        elif holding_share > 0:
            current_profit_percent = (row['Close'] - (cost / holding_share)) / (cost / holding_share)
            for level in monitor_levels:
                if current_profit_percent >= level:
                    max_profit_level = max(max_profit_level, level)
            if use_trailing_stop and max_profit_level > 0:
                next_level = max_profit_level - trailing_stop_percent
                if current_profit_percent < next_level:
                    sell(row)
                    buy_times = 0
                    investment_amount = initial_investment
                    max_profit_level = 0
                    continue
            elif not use_trailing_stop and current_profit_percent >= stop_profit_percent:
                sell(row)
                buy_times = 0
                investment_amount = initial_investment
                continue
        else:
            continue
        
    if holding_share != 0:
        row = stock_data.iloc[-1]
        sell(row)
        update_record()

    print('Rate of return:', profit / initail_cash * 100)
    return record, buy_dates, sell_dates

def main():
    def on_submit():
        try:
            initial_cash = float(initial_cash_entry.get())
            threshold = float(threshold_entry.get()) / 100
            initial_investment = float(initial_investment_entry.get())
            max_buy_times = int(max_buy_times_entry.get())
            use_trailing_stop = use_trailing_stop_var.get()
            trailing_stop_percent = float(trailing_stop_percent_entry.get()) / 100 if use_trailing_stop else 0
            stop_profit_percent = float(stop_profit_percent_entry.get()) / 100
            buy_multiplier = float(buy_multiplier_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid values.")
            return

        try:
            conn = connect_sql_server()
        except Exception as e:
            print(e)
            return

        stock_codes = stock_code.split(',')
        for code in stock_codes:
            stock_data = query_stock_data(conn, code)
            print(code)
            record, buy_dates, sell_dates = simulate_martingale_strategy(stock_data, threshold, initial_investment, initial_cash, max_buy_times, use_trailing_stop, trailing_stop_percent, stop_profit_percent, buy_multiplier)

        conn.close()
        messagebox.showinfo("Simulation Complete", "The simulation has been completed.")

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

    def toggle_trailing_stop(*args):
        if use_trailing_stop_var.get():
            trailing_stop_percent_entry.config(state='normal')
        else:
            trailing_stop_percent_entry.config(state='disabled')

    validate_float_command = root.register(validate_float)

    ttk.Label(root, text="Initial Cash").grid(column=0, row=0, padx=10, pady=5)
    initial_cash_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    initial_cash_entry.grid(column=1, row=0, padx=10, pady=5)

    ttk.Label(root, text="Threshold (%)").grid(column=0, row=1, padx=10, pady=5)
    threshold_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    threshold_entry.grid(column=1, row=1, padx=10, pady=5)

    ttk.Label(root, text="Initial Investment").grid(column=0, row=2, padx=10, pady=5)
    initial_investment_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    initial_investment_entry.grid(column=1, row=2, padx=10, pady=5)

    ttk.Label(root, text="Max Buy Times").grid(column=0, row=3, padx=10, pady=5)
    max_buy_times_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    max_buy_times_entry.grid(column=1, row=3, padx=10, pady=5)

    use_trailing_stop_var = tk.BooleanVar()
    use_trailing_stop_check = ttk.Checkbutton(root, text="Use Trailing Stop", variable=use_trailing_stop_var)
    use_trailing_stop_check.grid(column=0, row=4, columnspan=2, padx=10, pady=5)
    use_trailing_stop_var.trace_add('write', toggle_trailing_stop)

    ttk.Label(root, text="Trailing Stop (%)").grid(column=0, row=5, padx=10, pady=5)
    trailing_stop_percent_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    trailing_stop_percent_entry.grid(column=1, row=5, padx=10, pady=5)
    trailing_stop_percent_entry.config(state='disabled')

    ttk.Label(root, text="Stop Profit (%)").grid(column=0, row=6, padx=10, pady=5)
    stop_profit_percent_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    stop_profit_percent_entry.grid(column=1, row=6, padx=10, pady=5)

    ttk.Label(root, text="Buy Multiplier").grid(column=0, row=7, padx=10, pady=5)
    buy_multiplier_entry = ttk.Entry(root, validate="key", validatecommand=(validate_float_command, '%P'))
    buy_multiplier_entry.grid(column=1, row=7, padx=10, pady=5)

    submit_button = ttk.Button(root, text="Run Simulation", command=on_submit)
    submit_button.grid(column=0, row=8, columnspan=2, padx=10, pady=20)

    root.mainloop()

if __name__ == '__main__':
    main()
