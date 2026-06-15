#-------------------convert today's Miladi Date to Shamsi Date-----------------------
from datetime import date
from persiantools.jdatetime import JalaliDate

# Get today's date
today = date.today()

# Convert to Persian date
persian_date = JalaliDate.to_jalali(today.year, today.month, today.day)

# Format the Persian date as "YYYY/MM/DD"
formatted_persian_date = persian_date.strftime("%Y/%m/%d")

# Print the Persian date
print("Today's Persian date:", formatted_persian_date)

#-------------------take password from environmental variables-----------------------
import os

# Retrieve password from environment variable
password = os.environ.get('spass')
print(password)

#-------------------------take password from user securely----------------------------
from stdiomask import getpass
password = getpass("Enter Password: ").strip()

#-------------------------encryptor / decryptor----------------------------
# Encryption function
def encrypt(plain_text, key):
  cipher_text = ""
  for i in range(len(plain_text)):
    char = plain_text[i]
    cipher_int = ord(char) + key
    cipher_text += chr(cipher_int)
  return cipher_text

# Decryption function
def decrypt(cipher_text, key):
  plain_text = ""
  for i in range(len(cipher_text)):
    char = cipher_text[i]
    plain_int = ord(char) - key
    plain_text += chr(plain_int)
  return plain_text

password = "sina.z@abramad.com"
key = 9999

# Encrypt
cipher = encrypt(password, key)
print(cipher) # n}pCvvtrneb

# Decrypt
plain = decrypt(cipher, key)
print(plain) # mypassword

#-------------------if user does not input anything for 5 seconds give it a def value -------------------

import time
import threading

# Function to check for user input
def check_input():
    global user_input
    user_input = input("say: ")

# Get the start time
start_time = time.time()

# Create a thread for checking user input
input_thread = threading.Thread(target=check_input)

# Start the input thread
input_thread.start()

# Wait for user input or until 500 seconds have elapsed
input_thread.join(timeout=5)

# Check if the input thread is still alive (i.e., no input received)
if input_thread.is_alive():
    # No input received, assign a default value
    user_input = "Default Value"
else:
    # Input received before 500 seconds elapsed
    elapsed_time = time.time() - start_time

# Print the value of user_input
print("User Input:", user_input)

#------------------- append a dictonary to another dictionary -------------------
To append a dictionary to another dictionary with the same keys, you can iterate over the keys of the source dictionary and update the target dictionary accordingly. Here's an example:


def append_dict(target_dict, source_dict):
    for key, value in source_dict.items():
        if key in target_dict:
            target_dict[key].append(value)
        else:
            target_dict[key] = [value]

# Example dictionaries
dict1 = {'key1': [1, 2, 3], 'key2': [4, 5, 6]}
dict2 = {'key1': [7, 8, 9], 'key3': [10, 11, 12]}

# Append dict2 to dict1
append_dict(dict1, dict2)

print(dict1)
Output:

{'key1': [1, 2, 3, 7, 8, 9], 'key2': [4, 5, 6], 'key3': [10, 11, 12]}
In this example, the append_dict() function takes two dictionaries as input: target_dict and source_dict. It iterates over the keys and values of the source_dict. If a key exists in the target_dict, it appends the corresponding value from the source_dict to the existing value list in the target_dict. If a key does not exist in the target_dict, it creates a new entry with the key and the value list from the source_dict.

You can use this append_dict() function to append one dictionary to another while merging the values with the same keys.




# ------------------- get latest file created in a folder -------------------
import os

commvault_reports_path = "C:/Users/sina.z/Desktop/Commvault Reports/"
# Get a list of all files in the folder
files = os.listdir(commvault_reports_path)
# Sort the files based on their creation time
sorted_files = sorted(files, key=lambda x: os.path.getctime(os.path.join(commvault_reports_path, x)), reverse=True)
# Get the latest file (first element in the sorted list)
latest_commvault_report = sorted_files[0]
# Print the latest file name
print("Latest file:", latest_commvault_report)

# extend dict if it has a list value that has less than 8 items
for key in my_dict:
    if len(my_dict[key]) < 8:
        my_dict[key].extend([None] * (8 - len(my_dict[key])))



# ------------------- Flatten List -------------------

# Original list with one-item lists
nested_list = [[1], [2], [3], [4], [5]]

# Flattened list
flattened_list = [item for sublist in nested_list for item in sublist]

# Print the flattened list
print(flattened_list)