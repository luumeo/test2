from binance.client import Client
import time, pytz, threading
from datetime import datetime, timedelta
import argparse

api_key = "GKiCn4hcHSlCAE"
api_secret = "DOBJK5Oqlu5L"
# Khởi tạo client với api_key và api_secret của bạn
client = Client(api_key, api_secret)
sell_amount = {}  # Số tiền cần bán bớt tính theo $
symbol_percentages = {}
lenhrune = {}
xuat = {}
lay_tokenbandau = {}
command_entered = False


def get_min_quantity(symbol):
    try:
        exchange_info = client.futures_exchange_info()
        filters = next(filter(lambda x: x['symbol'] == symbol, exchange_info['symbols']))
        quantity_precision = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', filters['filters']))['stepSize']
        min_sluong = float(quantity_precision)
        return min_sluong
    except Exception as e:
        print(f"lấy giới hạn số lượng bị lỗi: {e}")
        return None


def mua(symbol, amount):
    try:
        # Thực hiện lệnh mua
        order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=amount
        )
        print(f"Mua: {amount} {symbol} tại giá market")
        return True
    except Exception as e:
        print(f"Gửi lệnh mua bị lỗi: {e}")
        return False


def ban(symbol, amount):
    try:
        # Thực hiện lệnh bán
        order = client.futures_create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=amount
        )
        print(f"Bán: {amount} {symbol} tại giá market")
        return True
    except Exception as e:
        print(f"Gửi lệnh bán bị lỗi: {e}")
        return False


while True:
    # try:
    vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time_vietnam = datetime.now(vietnam_timezone)
    giovn = current_time_vietnam.strftime("%d-%m-%Y %H:%M:%S")
    lenh = [obj for obj in client.futures_account()['positions'] if float(obj['positionAmt']) != 0]
    # print(lenh)
    for position in lenh:
        
        symbol = position['symbol']
        if symbol not in lay_tokenbandau:
            lay_tokenbandau[symbol] = float(position['positionAmt'])
        time.sleep(2)
        sell_amount[symbol] = 15
        ticker = client.futures_symbol_ticker(symbol=symbol)
        # print(ticker['price'])
        unrealized_profit = float(position['unrealizedProfit'])
        initial_margin = float(position['initialMargin'])
        gia_htai = float(ticker['price'])
        if symbol not in symbol_percentages:
            symbol_percentages[symbol] = {'dca_percentage': 0.05, 'sell_percentage': 0.10}
            lenhrune[symbol] = {'tinhtruoc': "danhlen", 'tinhsau': 'danhlen'}
        if 'dca_percentage' in symbol_percentages[symbol]:
            dca_percentage = symbol_percentages[symbol]['dca_percentage']
        elif 'dca_percentage' not in symbol_percentages[symbol]:
            dca_percentage = symbol_percentages[symbol].get('dca_percentage')
        if 'sell_percentage' in symbol_percentages[symbol]:
            sell_percentage = symbol_percentages[symbol]['sell_percentage']
        elif 'sell_percentage' not in symbol_percentages[symbol]:
            sell_percentage = symbol_percentages[symbol].get('sell_percentage')
        tinhtruoc = lenhrune[symbol]['tinhtruoc']
        tinhsau = lenhrune[symbol]['tinhsau']
        # amount = sell_amount / gia_htai
        time.sleep(2)
        kkk = get_min_quantity(symbol)
        meo = len(str(kkk).split('.')[1])
        if meo == 1:
            meo = 0
        amount = round((sell_amount[symbol] / gia_htai), meo)
        if amount == float(position['positionAmt']):
            amount = round(((sell_amount[symbol] + 3) / gia_htai), meo)
        gioihan = float(position["positionAmt"]) * gia_htai
        
        # print(amount)
        if float(position['positionAmt']) > 0:
            tinhsau = 'danhlen'
            vithe = "Long"
            
            if unrealized_profit < 0 and abs(unrealized_profit) > initial_margin * (dca_percentage or float(dca_percentage)) and (gioihan < 200):
                print(symbol,lay_tokenbandau[symbol], position["positionAmt"])
                if mua(symbol, amount):
                    symbol_percentages[symbol]['dca_percentage'] += 0.08
                    if symbol_percentages[symbol]['sell_percentage'] > 0.05:
                        symbol_percentages[symbol]['sell_percentage'] -= 0.05
                        sell_amount[symbol] += 1
                    print(
                        f"Tỉ lệ % cặp {symbol} cho lần DCA tiếp theo: {symbol_percentages[symbol]['dca_percentage'] * 100}")
                    print(
                        f"Mức bán cặp {symbol} được chỉnh lại mức: {symbol_percentages[symbol]['sell_percentage'] * 100}")
                    print(f"Giờ cập nhật {symbol}: {giovn}")

            elif unrealized_profit > 0 and unrealized_profit > initial_margin * (sell_percentage or float(sell_percentage)):
                if amount + lay_tokenbandau[symbol] <= float(position['positionAmt']):
                    print(symbol,lay_tokenbandau[symbol], position["positionAmt"])
                    if ban(symbol, amount):
                        symbol_percentages[symbol]['sell_percentage'] += 0.08
                        if symbol_percentages[symbol]['dca_percentage'] > 0.05:
                            symbol_percentages[symbol]['dca_percentage'] -= 0.05
                            sell_amount[symbol] += 1
                        print(
                            f"Tỉ lệ % cặp {symbol} cho lần CHỐT BỚT tiếp theo: {symbol_percentages[symbol]['sell_percentage'] * 100}")
                        print(
                            f"Mức dca cặp {symbol} được chỉnh lại mức: {symbol_percentages[symbol]['dca_percentage'] * 100}")
                        print(f"Giờ cập nhật {symbol}: {giovn}")
                elif float(position['positionAmt']) <= amount and float(position['positionAmt']) <= lay_tokenbandau and unrealized_profit >= 8:
                    ban(symbol, lay_tokenbandau[symbol])
            # if lay_tokenbandau[symbol] * 2 > float(position["positionAmt"]):
            #     ban(symbol, lay_tokenbandau[symbol])
        if float(position['positionAmt']) < 0:
            tinhsau = 'danhxuong'
            vithe = "Short"
            if unrealized_profit < 0 and abs(unrealized_profit) > initial_margin * (dca_percentage or float(dca_percentage)) and (gioihan < 200):
                print(symbol,lay_tokenbandau[symbol], position["positionAmt"])
                if ban(symbol, amount):
                    symbol_percentages[symbol]['dca_percentage'] += 0.08
                    if symbol_percentages[symbol]['sell_percentage'] > 0.05:
                        symbol_percentages[symbol]['sell_percentage'] -= 0.05
                        sell_amount[symbol] += 1
                    print(
                        f"Tỉ lệ % cặp {symbol} cho lần DCA tiếp theo: {symbol_percentages[symbol]['dca_percentage'] * 100}")
                    print(
                        f"Mức bán cặp {symbol} được chỉnh lại mức: {symbol_percentages[symbol]['sell_percentage'] * 100}")
                    print(f"Giờ cập nhật {symbol}: {giovn}")
            elif unrealized_profit > 0 and unrealized_profit > initial_margin * (sell_percentage or float(sell_percentage)):
                if amount + lay_tokenbandau[symbol] <= float(position['positionAmt']):
                    print(symbol,lay_tokenbandau[symbol], position["positionAmt"])
                    if mua(symbol, amount):
                        symbol_percentages[symbol]['sell_percentage'] += 0.08
                        if symbol_percentages[symbol]['dca_percentage'] > 0.05:
                            symbol_percentages[symbol]['dca_percentage'] -= 0.05
                            sell_amount[symbol] += 1
                        print(
                            f"Tỉ lệ % cặp {symbol} cho lần CHỐT BỚT tiếp theo: {symbol_percentages[symbol]['sell_percentage'] * 100}")
                        print(
                            f"Mức dca cặp {symbol} được chỉnh lại mức: {symbol_percentages[symbol]['dca_percentage'] * 100}")
                        print(f"Giờ cập nhật {symbol}: {giovn}")
                elif float(position['positionAmt']) <= amount and float(position['positionAmt']) <= lay_tokenbandau and unrealized_profit >= 8:
            # if lay_tokenbandau[symbol] * 2 > float(position["positionAmt"]):
                    mua(symbol, lay_tokenbandau[symbol])
        if tinhtruoc != tinhsau:
            symbol_percentages[symbol]['dca_percentage'] = 0.05
            symbol_percentages[symbol]['sell_percentage'] = 0.1
            sell_amount[symbol] = 15
            print(f'Vị thế đã bị đảo. Vị thế hiện tại: {vithe} {symbol}')
        lenhrune[symbol]['tinhtruoc'] = tinhsau
        time.sleep(1)
        pass
    # except KeyboardInterrupt:
    #     break
    # except Exception as e:
    #     print(f"Lỗi khi xử lý tác vụ: {e}")

