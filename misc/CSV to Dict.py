import csv
from collections import defaultdict

# Open the CSV file and read its contents
my_dict = {}
with open('C:/Users/sina.z/Desktop/RahkaranAbriReport/Bah-1403/RA-Tag-Bah-1403.csv', newline='', encoding='utf-16-le') as csvfile:
    reader = csv.reader(csvfile)
    # Skip the header row if it exists
    next(reader, None)
    # Create a defaultdict to store the dictionary
    my_dict = defaultdict(list)
    # Loop through each row in the CSV file
    for row in reader:
        # Use the first column as the key
        key = row[0]
        # Use the rest of the columns as the value
        value = row[1:]
        # Add the value to the dictionary under the key
        my_dict[key].extend(value)

print(my_dict['RA-IRSobhan'])