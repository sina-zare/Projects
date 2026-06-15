import psycopg2

# Function to read data from file
def read_data_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        # Assuming each line contains name and URL separated by a comma
        data = [line.strip().split(',') for line in lines]
    return data

# Function to insert data into the database
def insert_data_into_database(data):
    conn = psycopg2.connect(
        dbname='url_monitor',
        user='postgres',
        password='P@ssw0rd',
        host='localhost',
        port='5432'
    )
    cursor = conn.cursor()
    for name, url in data:
        cursor.execute("INSERT INTO urls (name, url) VALUES (%s, %s)", (name, url))
    conn.commit()
    conn.close()

# File path containing the data
file_path = 'URLs.txt'

# Read data from file
data = read_data_from_file(file_path)

# Insert data into the database
insert_data_into_database(data)