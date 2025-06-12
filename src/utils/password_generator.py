import secrets
import string
import os

def generate_strong_password(length=24):
    """Generate a strong, random password."""
    if length < 12:
        raise ValueError("Password length should be at least 12 characters for security.")

    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for i in range(length))
    return password

if __name__ == "__main__":
    generated_password = generate_strong_password()
    temp_password_file = "temp_db_password.txt"
    with open(temp_password_file, "w") as f:
        f.write(generated_password)
    print(f"Generated password saved to {temp_password_file}. Please read it and then I will delete it.") 