import secrets
import string
def generate_password(length=15):
    if length < 4:
        raise ValueError("Password length must be at least 4 to include all required character types.")

    # Define character sets
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits

    # Fill the rest of the password length with a mix of all characters
    #all_chars = lowercase + uppercase + digits + symbols
    all_chars = lowercase + uppercase + digits

    password = []
    password += [secrets.choice(all_chars) for _ in range(length)]

    # Shuffle the result to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)

for i in range(1,8):
    print(f"{generate_password(16)}:{generate_password(16)}")