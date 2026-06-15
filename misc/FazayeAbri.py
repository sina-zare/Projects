import time
import os
import pandas as pd

raw_customer_data = pd.read_excel("E:\\IaaC\\FazayeAbri\\data.xlsx", dtype=str)
columns_indices = [0, 1, 2, 3, 4, 6, 7, 8]
extracted_data = [list(row.iloc[columns_indices]) for index, row in raw_customer_data.iterrows()]
better_extracted_data = []

for customer in extracted_data:

    customer[1] = str(customer[1]).zfill(10)

    customer[2] = str(customer[2]).zfill(11)

    if str(customer[4]) == 'nan':
        customer[4] = 'مشترک اکانت داشته اما اصلا فضای ابری ای خریداری نکرده است'
    elif str(customer[4]).startswith('{'):
        customer[4] = f'مشترک دارای فضای ابری به صورت زیر میباشد\n    {str(customer[4])}'

    if str(customer[5]) != '0':  # Adding Thousands seperator
        customer[5] = f"{int(str(int(float(customer[5])))[:-1]):,}"

    if str(customer[6]).startswith('تماس'):
        customer[6] = 'آقای "امیر رضایی" شخصا با ایشان تماس گرفته اند'
    elif str(customer[6]).startswith('بررسی'):
        customer[6] = 'آقای "امیر رضایی" شخصا این مورد رو بررسی کرده اند'
    elif str(customer[6]).startswith('اعلام سرنخ'):
        customer[6] = 'مشترک باید مجدد در سامانه ثبت نام نمایند'
    elif str(customer[6]) == 'انتقال':
        customer[6] = 'مشترک به سامانه جدید منتقل شده و دارای حساب فعال میباشد و باقی مانده کیف پول ایشان مثبت میباشد'
    elif str(customer[6]).startswith('انتقال با مانده واقعی'):
        customer[
            6] = 'مشترک به سامانه جدید منتقل شده و دارای حساب فعال میباشد ولی کیف پول ایشان تازه منفی شده و مقدار آن کمتر از صد هزار تومان میباشد'
    elif str(customer[6]).startswith('حذف'):
        customer[
            6] = 'مشترک تنها در سامانه قبلی حساب ایجاد نموده و هیچ فضایی خریداری نکرده، ایشان مجدد میبایست در سامانه جدید ثبت نام نمایند'
    elif str(customer[6]).startswith('عدم انتقال'):
        customer[
            6] = 'مشترک فضای ابری فعال داشته و تا 10 خرداد دسترسی به این فضا را دارد، اما چون کیف پول ایشان بالای یک ماه است که منفی شده\n و پرداختی صورت نگرفته، دسترسی به سامانه جدید را نداشته و حتی امکان ثبت نام را نیز ندارد، اگر مشترک قصد تسویه حساب دارد\n باید به تیم محصول اطلاع داده شود و مشترک میتواند ظرف گذشت 24 ساعت کاری جهت تسویه به سامانه وارد شود'

    if str(customer[7]) == 'nan':
        customer[7] = "ندارد"

while True:
    flag = 0
    input_data = input("Enter one of the following\n\nNational Code / Phone No / Email Address\n\n--> ")
    os.system('cls' if os.name == 'nt' else 'clear')

    for customer_data in extracted_data:
        # print(customer_data[2])
        if input_data == customer_data[1] or input_data == customer_data[2] or input_data == customer_data[3]:
            output = f"""
    {40 * '~'}
    نام: {customer_data[0]}
    کد ملی: {customer_data[1]}
    شماره موبایل: {customer_data[2]}
    ایمیل: {customer_data[3]}

    میزان فضای ابری: {customer_data[4]}
    اعتبار کیف پول: {customer_data[5]}

    شرح وضعیت: {customer_data[6]}

    توضیحات تکمیلی: {customer_data[7]}

    {40 * '~'}
            """
            print(output)
            flag = 1
            input("\n\nPress Enter to Continue.")
            os.system('cls' if os.name == 'nt' else 'clear')

    if flag == 0:
        print("مشتری با این اطلاعات یافت نشد")
        time.sleep(3)
        os.system('cls' if os.name == 'nt' else 'clear')

