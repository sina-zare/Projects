import MetaTrader5 as mt5
import pandas as pd
import sinzi
import time
import jdatetime
import asyncio
import mplfinance as mpf
import matplotlib
from telegram import Bot
import os

# Use a non-interactive backend
matplotlib.use('Agg')

# Symbol Info
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M1

# Initialize Telegram Bot
bot = Bot(token='7241117184:AAGY-0-JFJHFoE-AXS2sOTvMIhCLWQqBQew')
chat_ids = [['49487552', 'Sina Zare'], ['118865253', 'Soroush Zare']]

# Initialize MT5 connection
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

def generate_chart(candles):
    # Convert the data to a DataFrame
    df = pd.DataFrame(candles)
    # Convert the 'time' column to datetime and set the timezone to +3:00
    df['time'] = pd.to_datetime(df['time'], unit='s').dt.tz_localize('Etc/GMT-3')
    # Adjust the timezone to +3:30
    df['time'] = df['time'] + pd.Timedelta(minutes=30)
    # Remove timezone information after conversion
    df['time'] = df['time'].dt.tz_localize(None)
    df.set_index('time', inplace=True)

    # Plot candlestick chart
    mpf.plot(df, type='candle', style='charles', title='XAUUSD 5-Minute Candlesticks', ylabel='Price',
             savefig='chart.png')

async def monitor_candles():
    while True:
        # Fetch the latest candle
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 11)  # Fetch the last 10 bars to include the most recent completed bar

        if bars is None or len(bars) < 2:
            print("Failed to fetch data")
            continue

        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # Check the last completed candle
        last_candle = df.iloc[-2]

        if sinzi.is_pin_bar(last_candle):

            if bars is not None and bars.size > 0:
                # Generate chart
                generate_chart(bars[:-1])

                # Ensure the file is properly saved
                if os.path.exists('chart.png') and os.path.getsize('chart.png') > 0:
                    print(30 * '~')
                    # Send chart image to Telegram
                    for userid in chat_ids:
                        with open('chart.png', 'rb') as photo:
                            await bot.send_photo(chat_id=userid[0], photo=photo)
                            print(f"photo sent for {userid[1]}")
                else:
                    print("Chart file is empty or does not exist")
            print('---')
            today_date_jalali_full = '~~~~ ' + str(jdatetime.datetime.now())[:-7] + ' ~~~~'
            candle_miladi_date = str(last_candle['time'])[:10]
            candle_plus3_00_time = str(last_candle['time'])[11:]

            shamsi_date, shamsi_time = sinzi.convert_miladi_to_shamsi(candle_miladi_date, candle_plus3_00_time)
            body = f"{today_date_jalali_full}\n\nSymbol: {symbol}\nTime Frame: {timeframe} Min\nPin Bar Pattern Formed at {shamsi_time}\n\nConsider making positions.\n\n~~~~ ~~~~ ~~~~~ ~~~~ ~~~~ "

            # Send Text data to chat
            for userid in chat_ids:
                await bot.send_message(chat_id=userid[0], text=body)
                print(f"text sent for {userid[1]}")
            print(30 * '~' + '\n')
        await asyncio.sleep(60)

try:
    asyncio.run(monitor_candles())
except KeyboardInterrupt:
    print("Monitoring stopped")
finally:
    # Shutdown MT5 connection
    mt5.shutdown()
