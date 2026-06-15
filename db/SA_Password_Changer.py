try:
    import pyodbc

    db_connection = pyodbc.connect(
        'DRIVER={SQL Server};'
        'SERVER=localhost;'
        'UID=sa;'
        'PWD=B8HS5gd4sxp047Kgq;'
    )

    # Create a cursor object
    cursor = db_connection.cursor()

    # Execute SQL query to change the SA password
    new_password = 'Xx123456'
    cursor.execute("ALTER LOGIN sa WITH PASSWORD='" + new_password + "';")
    db_connection.commit()

    # Close the cursor and connection
    cursor.close()
    db_connection.close()

    print("SA password changed successfully!")
    input()

except Exception as e:
    input(e)

