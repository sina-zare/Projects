import MetaTrader5 as mt5
import pandas as pd
import time
import datetime
import pytz
import jdatetime
import sinzi

# Initialize MT5 connection
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# Set symbol and timeframe
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M5  # 1 hour timeframe

def monitor_candles():
    while True:
        # Fetch the latest candle
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 5000)  # Fetch the last 2 bars to include the most recent completed bar

        if bars is None or len(bars) < 2:
            print("Failed to fetch data")
            continue

        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # Check the last completed candle
        #last_candle = df.iloc[-2]

        for i in range(len(df) - 1):
            if i == (len(df) - 3):
                break
            candle1 = df.iloc[i]
            candle2 = df.iloc[i + 1]
            candle3 = df.iloc[i + 2]
            candle4 = df.iloc[i + 3]


            if sinzi.is_bearish_engulfing_3x(candle1, candle2, candle3, candle4):

                print(f"Bullish Engulfing Formed  --> Original: {candle4['time']}")
                #time.sleep(60)
        break

try:
    monitor_candles()
except KeyboardInterrupt:
    print("Monitoring stopped")
finally:
    # Shutdown MT5 connection
    mt5.shutdown()
