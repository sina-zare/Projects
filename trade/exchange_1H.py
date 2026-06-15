import MetaTrader5 as mt5
import pandas as pd
import time
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import datetime
import pytz
import jdatetime

def convert_miladi_to_shamsi(miladi_date_str, time_str):
    # Define the format for input date and time
    miladi_format = "%Y-%m-%d %H:%M:%S"

    # Combine date and time strings into a single datetime string
    miladi_datetime_str = f"{miladi_date_str} {time_str}"

    # Parse the datetime string into a datetime object
    miladi_datetime = datetime.datetime.strptime(miladi_datetime_str, miladi_format)

    # Define the +3:00 timezone
    timezone_3 = pytz.timezone('Etc/GMT-3')

    # Localize the datetime object to the +3:00 timezone
    localized_datetime = timezone_3.localize(miladi_datetime)

    # Convert the localized datetime to the +3:30 timezone
    timezone_330 = pytz.timezone('Asia/Tehran')
    converted_datetime = localized_datetime.astimezone(timezone_330)

    # Extract the date part for Shamsi conversion
    converted_date = converted_datetime.date()

    # Convert the Gregorian date to Shamsi date
    shamsi_date = jdatetime.date.fromgregorian(date=converted_date)

    # Format the Shamsi date and time to desired output format
    shamsi_date_str = shamsi_date.strftime("%Y-%m-%d")
    time_str_330 = converted_datetime.strftime("%H:%M:%S")

    return shamsi_date_str, time_str_330

def email_sender(username, password, email_receivers, email_cc, subject, direction, html_body, mail_server='mail.abramad.com'):

    try:
        # Create a multipart message object
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = email_receivers
        msg['CC'] = email_cc
        msg['Subject'] = subject

        ##############################################
        ######### HTML Body Begin For Email ##########
        html_line_break = '''
                            <p><br></p>
                        '''
        html_msg_1 = f'''
                        <html dir={direction}>
                          <body>
                        '''
        html_msg_2 = f'''
                            <p  style="font-family: DiodrumArabic-Regular">{html_body}</p>
                        '''

        html_msg_3 = f'''
                                <p  style="font-family: DiodrumArabic-Regular"><b>Sina Zare<br>Support Team Lead<br>Operation Team</b></p>
                            '''
        html_msg_4 = '''
                          </body>
                        </html>
                        '''
        ######### HTML Body End For Email ##########
        ############################################

        email_body = html_msg_1 + html_msg_2 + html_line_break + html_line_break + html_msg_4
        msg.attach(MIMEText(email_body, 'html'))

        # Connect to the SMTP server and send the email on 587 TCP
        smtp_server = mail_server
        smtp_port = 587

        # Send email function
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, email_receivers.split(",") + email_cc.split(','), msg.as_string())

    except Exception as err:
        print(f"Function Error: {err}")

# Credentials
from cryptography.fernet import Fernet
def decryptor(enc_env_var, key_env_var):

    # Load the key
    key = os.environ.get(key_env_var)
    encryption_key = Fernet(key)
    encrypted_password = (os.environ.get(enc_env_var)).encode()
    # Decrypt Data
    decrypted_password = encryption_key.decrypt(encrypted_password.decode())

    #print(f"Decryped Text: {decrypted_password}")
    return decrypted_password.decode()
username = decryptor("enc_sinaz_abramad","key_sinaz_abramad")
password = decryptor("enc_sinaz_pass","key_sinaz_pass")

# Initialize MT5 connection
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# Set symbol and timeframe
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_H1  # 60 Mins timeframe


def is_pin_bar(candle):
    open_price = candle['open']
    close_price = candle['close']
    high_price = candle['high']
    low_price = candle['low']

    body_length = abs(close_price - open_price)
    upper_wick = high_price - max(open_price, close_price)
    lower_wick = min(open_price, close_price) - low_price
    candle_length = high_price - low_price

    # Avoid division by zero
    if candle_length == 0 or body_length == 0:
        return False

    # Define the pin bar conditions
    body_to_candle_ratio = body_length / candle_length
    wick_to_body_ratio = max(upper_wick, lower_wick) / body_length

    # Check if the body is in the upper half of the candle
    body_upper_than_center_condition = (open_price + close_price) / 2 > (high_price + low_price) / 2

    # Check for perfect pin bar (no upper wick)
    perfect_pin_bar_condition = upper_wick == 0

    # Check if it matches a pin bar, body_upper_than_center_condition conditions
    is_pin_bar = body_to_candle_ratio < 0.3 and wick_to_body_ratio > 2.0
    body_is_upper_than_center = body_upper_than_center_condition
    is_perfect_pin_bar = perfect_pin_bar_condition

    return (is_pin_bar and body_is_upper_than_center) or (
                is_pin_bar and body_is_upper_than_center and is_perfect_pin_bar)

def monitor_candles():
    while True:
        # Fetch the latest candle
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 2)  # Fetch the last 2 bars to include the most recent completed bar

        if bars is None or len(bars) < 2:
            print("Failed to fetch data")
            continue

        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        # Check the last completed candle
        last_candle = df.iloc[-2]

        if is_pin_bar(last_candle):

            today_date_jalali_full = '~~~~~~~~~~ ' + str(jdatetime.datetime.now())[:-7] + ' ~~~~~~~~~~'
            candle_miladi_date = str(last_candle['time'])[:10]
            candle_plus3_00_time = str(last_candle['time'])[11:]

            shamsi_date, shamsi_time = convert_miladi_to_shamsi(candle_miladi_date, candle_plus3_00_time)

            print(f"Pin Bar Formed on {symbol} at {shamsi_date} {shamsi_time} --> Original: {last_candle['time']}")
            body = f"<b>{today_date_jalali_full}</b><br><br>Symbol: <b>{symbol}</b><br>Time Frame: 1H<br>Pin Bar Pattern Formed on <b>{symbol}</b> at <b>{shamsi_time}</b><br>Consider Buy/Sell Opportunities.<br><br>Cheers"
            email_sender(username, password, "soroush.theeee1st@gmail.com", "",
                         f"Pin Bar Formed | {shamsi_date} | 1H", "ltr", body,
                         "mail.systemgroup.net")
        # soroushsilver91891sz.gimsl.com@gmail.com
        # Wait for 60 minutes before checking again
        time.sleep(3600)

try:
    monitor_candles()
except KeyboardInterrupt:
    print("Monitoring stopped")
finally:
    # Shutdown MT5 connection
    mt5.shutdown()
