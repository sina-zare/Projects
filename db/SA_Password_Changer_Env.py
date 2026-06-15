try: # Module Importing
    from cryptography.fernet import Fernet
    import time
    import string
    import secrets
    import pyodbc
    import subprocess

except Exception as e:
    print("Error in Importing Modules.\n", e)
    time.sleep(10)


# Function Definition
def generate_password(length=16):
    if length < 4:
        raise ValueError("Password length must be at least 4 to include all required character types.")

    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    #symbols = "!@#$%^&*()-_=+"

    # Ensure at least one character from each category
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        #secrets.choice(symbols)
    ]

    # Fill the rest of the password length with a mix of all characters
    all_chars = lowercase + uppercase + digits # + symbols
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle the result to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def encryptor_env(password, env_enc, env_key):
    # Generate a key and store it securely
    key = Fernet.generate_key()

    # Encrypt sensitive data
    encryption_key = Fernet(key)
    encrypted_password = encryption_key.encrypt(password.encode())

    # Saving Enc_Password and key to System Envs
    subprocess.run(['setx', '/M', env_enc, f'{str(encrypted_password)[2:-1]}'], check=True)
    subprocess.run(['setx', '/M', env_key, f'{str(key)[2:-1]}'], check=True)

    print(f"Password Encrypted.")

def sa_password_changer(old_password, new_password):
    try:
        db_connection = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=localhost;'
            'UID=sa;'
            f'PWD={old_password};' #B8HS5gd4sxp047Kgq
        )

        # Create a cursor object
        cursor = db_connection.cursor()

        # Execute SQL query to change the SA password
        cursor.execute("ALTER LOGIN sa WITH PASSWORD='" + new_password + "';")
        db_connection.commit()

        # Close the cursor and connection
        cursor.close()
        db_connection.close()

        print("SA password changed successfully!")

    except Exception as e:
        print("Error in sa_password_changer Function.")
        print("An error occurred:", e)
        time.sleep(10)



try: # Main App

    # Change Current SA Password
    old_sa_password = 'B8HS5gd4sxp047Kgq'
    new_sa_password = generate_password(17)
    #print(new_sa_password)
    sa_password_changer(old_sa_password, new_sa_password)

    # Saving Encrypted Password to System Envs
    encryptor_env(new_sa_password, "sgsp", "sgsk")


except Exception as e:
    print("An error occurred:", e)
    time.sleep(10)