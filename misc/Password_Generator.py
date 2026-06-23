import string
import secrets

def generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


# Generate a password
password = generate_password(30)
print("Generated Password:", password)
