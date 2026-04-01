import hashlib
import re


PASSWORD_RULE_MESSAGE = (
    "password must include at least one uppercase letter and one special character."
)


def validate_password_complexity(password: str, error_type=ValueError) -> None:
    if not (
        isinstance(password, str)
        and re.search(r"[A-Z]", password)
        and re.search(r"[^A-Za-z0-9]", password)
    ):
        raise error_type(PASSWORD_RULE_MESSAGE)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def password_matches(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
