"""Password hashing utilities using Argon2."""
from __future__ import annotations


from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Initialize Argon2 password hasher with secure defaults
_password_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    if not password or not password.strip():
        raise ValueError("Password cannot be empty")
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    try:
        _password_hasher.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    if not hashed_password:
        return True
    try:
        return _password_hasher.check_needs_rehash(hashed_password)
    except Exception:
        return True