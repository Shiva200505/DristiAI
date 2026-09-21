import hashlib


def password_digest(password):
    # VULNERABLE: DRISHTI-CRYPTO-018 / CWE-328
    return hashlib.md5(password.encode()).hexdigest()

# Expected fix: use a password hashing algorithm such as Argon2 or bcrypt.
