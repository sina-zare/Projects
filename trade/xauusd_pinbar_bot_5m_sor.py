try:
    import MetaTrader5 as mt5
    import pandas as pd
    from sinzi import is_pin_bar, is_perfect_pin_bar, convert_miladi_to_shamsi, sinzi_logo
    import time
    import jdatetime
    import asyncio
    import mplfinance as mpf
    import matplotlib
    from telegram import Bot
    import os

    sinzi_logo()

    # Use a non-interactive backend
    matplotlib.use('Agg')

    # Symbol Info
    log_path = "xauusd_pinbar_5m.log"
    image_path = "xauusd_pinbar_5m.png"
    symbol = "XAUUSD"
    timeframe = mt5.TIMEFRAME_M5
    sleep_time = int(timeframe) * 60

    # Initialize Telegram Bot
    bot = Bot(token='7319275718:AAHDECb-pMEPyjtuFpSAX0DJOL4h85M8KR8')
    chat_ids = [['49487552', 'Sina Zare'], ['118865253', 'Soroush Zare']]

    # Initialize MT5 connection
    if not mt5.initialize():
        print("MT5 initialize() failed")
        with open(log_path, "a") as log:
            log.write("MT5 initialize() failed" + "\n")
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
        mpf.plot(df, type='candle', style='charles', title=f'{symbol} {timeframe}-Minute Candlesticks', ylabel='Price',
                 savefig=f'{image_path}')


    async def monitor_candles():
        while True:
            try:
                # Defining when the app should work.
                # Get the current Persian date and time
                current_persian_datetime = jdatetime.datetime.now()

                # Extract the week name
                persian_week_name = current_persian_datetime.strftime('%A')

                # Extract the time
                persian_time = current_persian_datetime.strftime('%H:%M:%S')
                persian_hour = int(persian_time.split(":")[0])

                if persian_week_name != "Saturday" and persian_week_name != "Sunday":
                    if 9 <= persian_hour < 23:

                        # Fetch the latest candle
                        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0,
                                                       12)  # Fetch the last 10 bars to include the most recent completed bar

                        if bars is None or len(bars) < 2:
                            print("Failed to fetch data")
                            with open(log_path, "a") as log:
                                log.write("Failed to fetch data" + "\n")
                            continue

                        # Convert to DataFrame
                        df = pd.DataFrame(bars)
                        df['time'] = pd.to_datetime(df['time'], unit='s')

                        # Check the last completed candle
                        last_candle = df.iloc[-2]

                        perfect_pinbar_flag = 0

                        if is_pin_bar(last_candle):

                            if bars is not None and bars.size > 0:
                                # Generate chart
                                generate_chart(bars[:-1])

                                # Ensure the file is properly saved
                                if os.path.exists(image_path) and os.path.getsize(image_path) > 0:

                                    today_date_jalali_full = '~~~~ ' + str(jdatetime.datetime.now())[:-7] + ' ~~~~'
                                    candle_miladi_date = str(last_candle['time'])[:10]
                                    candle_plus3_00_time = str(last_candle['time'])[11:]
                                    shamsi_date, shamsi_time = convert_miladi_to_shamsi(candle_miladi_date, candle_plus3_00_time)

                                    # Check if it is Perfect Pinbar
                                    if is_perfect_pin_bar(last_candle):

                                        perfect_pinbar_body = f"{today_date_jalali_full}\n\nSymbol: {symbol}\nTime Frame: {timeframe} Min\nPerfect Pinbar Pattern Formed at {shamsi_time}\n\n~~~~ ~~~~ ~~~~~ ~~~~ ~~~~ "

                                        print(10 * '~' + f'{symbol} {timeframe}M' + 10 * '~')
                                        with open(log_path, "a") as log:
                                            log.write(10 * '~' + f'{symbol} {timeframe}M' + 10 * '~' + "\n")
                                        print(f'perfect pinbar at {shamsi_date} {shamsi_time}\n')
                                        with open(log_path, "a") as log:
                                            log.write(f"perfect pinbar at {shamsi_date} {shamsi_time}" + "\n")

                                        # Send chart image to Telegram
                                        for userid in chat_ids:
                                            with open(image_path, 'rb') as photo:
                                                await bot.send_photo(chat_id=userid[0], photo=photo)
                                                print(f"photo sent for {userid[1]}")
                                                with open(log_path, "a") as log:
                                                    log.write(f"photo sent for {userid[1]}" + "\n")
                                            # Send Text data to chat
                                            await bot.send_message(chat_id=userid[0], text=perfect_pinbar_body)
                                            print(f"text sent for {userid[1]}")
                                            with open(log_path, "a") as log:
                                                log.write(f"text sent for {userid[1]}" + "\n")

                                        perfect_pinbar_flag = 1


                                    if perfect_pinbar_flag == 0:

                                        pinbar_body = f"{today_date_jalali_full}\n\nSymbol: {symbol}\nTime Frame: {timeframe} Min\nPinbar Pattern Formed at {shamsi_time}\n\n~~~~ ~~~~ ~~~~~ ~~~~ ~~~~ "

                                        print(10 * '~' + f'{symbol} {timeframe}M' + 10 * '~')
                                        with open(log_path, "a") as log:
                                            log.write(10 * '~' + f'{symbol} {timeframe}M' + 10 * '~' + "\n")
                                        print(f'pinbar at {shamsi_date} {shamsi_time}\n')
                                        with open(log_path, "a") as log:
                                            log.write(f'pinbar at {shamsi_date} {shamsi_time}\n' + "\n")

                                        # Send chart image to Telegram
                                        for userid in chat_ids:
                                            with open(image_path, 'rb') as photo:
                                                await bot.send_photo(chat_id=userid[0], photo=photo)
                                                print(f"photo sent for {userid[1]}")
                                                with open(log_path, "a") as log:
                                                    log.write(f"photo sent for {userid[1]}" + "\n")
                                            # Send Text data to chat
                                            await bot.send_message(chat_id=userid[0], text=pinbar_body)
                                            print(f"text sent for {userid[1]}")
                                            with open(log_path, "a") as log:
                                                log.write(f"text sent for {userid[1]}" + "\n")

                                else:
                                    print(f"{image_path} file is empty or does not exist")
                                    with open(log_path, "a") as log:
                                        log.write(f"{image_path} file is empty or does not exist" + "\n")
                                print(30 * '~' + '\n')
                                with open(log_path, "a") as log:
                                    log.write(30 * '~' + '\n' + "\n")

                        await asyncio.sleep(sleep_time)

            except Exception as e:
                print(f"Error: {e}")
                with open(log_path, "a") as log:
                    log.write(f"Error: {e}" + "\n")
                continue


    try:
        asyncio.run(monitor_candles())
    except KeyboardInterrupt:
        print("Monitoring stopped")
        with open(log_path, "a") as log:
            log.write("Monitoring stopped" + "\n")
    finally:
        # Shutdown MT5 connection
        mt5.shutdown()

except Exception as err:
    print(f"General Error: {err}")
    with open(log_path, "a") as log:
        log.write(f"General Error: {err}" + "\n")
    #input("\n...")