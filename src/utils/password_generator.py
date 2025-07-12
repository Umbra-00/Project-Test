import secrets
import string


def generate_strong_password(length=24):
    """Generate a strong, random password."""
    if length < 12:
        raise ValueError(
            "Password length should be at least 12 characters for security."
        )

    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(characters) for i in range(length))
    return password


if __name__ == "__main__":
    generated_password = generate_strong_password()
    print(f"Generated password: {generated_password}")
    print("Please copy this password. It will not be saved to a file.")
