import psycopg2

# Connect to PostgreSQL
connection = psycopg2.connect(
    host="localhost",
    database="url_monitoring",
    user="your_username",
    password="your_password"
)

# Create the URLs table
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            url VARCHAR(255) NOT NULL,
            status BOOLEAN,
            last_checked TIMESTAMP
        )
    """)

# Commit the changes and close the connection
connection.commit()
connection.close()
