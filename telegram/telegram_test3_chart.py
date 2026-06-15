import matplotlib.pyplot as plt
import MetaTrader5 as mt5
import asyncio
import mplfinance as mpf
from telegram import Bot
import pandas as pd
import jdatetime

# Initialize Telegram Bot
bot = Bot(token='7241117184:AAGY-0-JFJHFoE-AXS2sOTvMIhCLWQqBQew')


def retrieve_candlestick_data(symbol, timeframe, count):
    # Connect to MetaTrader 5
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return None

    # Request the last 10 candlesticks for XAUUSD in the 5-minute timeframe
    candles = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

    # Close the MetaTrader 5 connection
    mt5.shutdown()

    return candles


def generate_chart(candles):
    # Convert the data to a DataFrame
    df = pd.DataFrame(candles)

    # Convert the 'time' column to datetime and set the timezone to +3:00
    df['time'] = pd.to_datetime(df['time'], unit='s').dt.tz_localize('Etc/GMT-3')

    # Adjust the timezone to +3:30
    df['time'] = df['time'] + pd.Timedelta(minutes=30)

    # Remove timezone information after conversion
    df['time'] = df['time'].dt.tz_localize(None)

    print(df)
    df.set_index('time', inplace=True)

    # Plot candlestick chart
    mpf.plot(df, type='candle', style='charles', title='XAUUSD 5-Minute Candlesticks', ylabel='Price',
             savefig='chartz.png')


async def send_chart_to_telegram():
    # Retrieve candlestick data
    candles = retrieve_candlestick_data('XAUUSD', mt5.TIMEFRAME_M5, 10)

    if candles is not None and candles.size > 0:
        # Generate chart
        generate_chart(candles)

        # Send chart image to Telegram
        with open('chart.png', 'rb') as photo:
            await bot.send_photo(chat_id='49487552', photo=photo)
            await bot.send_sticker()


if __name__ == '__main__':
    asyncio.run(send_chart_to_telegram())
