import csv
import pandas as pd

# Filling Ticket HID for Abramad Support
sarv_data = []
sarv_csv_file = "C:/Users/sina.z/Desktop/Automation_Reports/Downtime/rawt.csv"
with open(sarv_csv_file, 'r', encoding='utf-8-sig') as read_file:
    reader = csv.reader(read_file)

    # Skip the first 8 lines
    for _ in range(8):
        next(reader)

    for row in reader:
        sarv_data.append([row[0], row[4]])


all_vms_info_agents_excel_file = "C:/Users/sina.z/Desktop/Automation_Reports/All_VMs_Info/Servers-Full-Report-Agents.xlsx"
raw_sms_data = pd.read_excel(all_vms_info_agents_excel_file, dtype=str)

#for hid in sarv_data:
#    # Filter rows where column 7 is equal to "x"
#    email_addresses = raw_sms_data[raw_sms_data.iloc[:, 20]]
#    print(email_addresses)

# Specify the column indices you want to extract (0-based index)
columns_indices = range(0, 22)

# Extract the specified columns from each row and store them in a list
extracted_data = [list(row.iloc[columns_indices]) for index, row in raw_sms_data.iterrows()]
print(extracted_data)
"""
for hid in sarv_data:

    for email in sms_email_data:

        if email[0].lower().strip() == hid[0].lower().strip():
            final_data_hid.append(hid[1])
            final_data_email.append(hid[0].lower())
            print(f"Matched: {hid[0].lower()}")


"""