import matplotlib.pyplot as plt
import MetaTrader5 as mt5
import asyncio
from telegram import Bot

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
    # Extract necessary data from candlestick data
    timestamps = [candle['time'] for candle in candles]
    closes = [candle['close'] for candle in candles]

    # Create a plot
    plt.plot(timestamps, closes)

    # Customize the plot (optional)
    plt.title('XAUUSD 5-Minute Candlesticks')
    plt.xlabel('Time')
    plt.ylabel('Close Price')

    # Save the plot as an image
    plt.savefig('chart.png')

    # Clear the plot
    plt.clf()

async def send_chart_to_telegram():
    # Retrieve candlestick data
    candles = retrieve_candlestick_data('XAUUSD', mt5.TIMEFRAME_M5, 10)

    if candles is not None and candles.size > 0:
        # Generate chart
        generate_chart(candles)

        # Send chart image to Telegram
        with open('chart.png', 'rb') as photo:
            await bot.send_photo(chat_id='49487552', photo=photo)

if __name__ == '__main__':
    asyncio.run(send_chart_to_telegram())
