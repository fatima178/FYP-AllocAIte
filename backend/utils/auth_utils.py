import hashlib
import re


PASSWORD_RULE_MESSAGE = (
    "password must be at least 6 characters and include at least one uppercase letter and one special character."
)


def validate_password_complexity(password: str, error_type=ValueError) -> None:
    # keep password rules in one place so register, settings and invites match
    if not (
        isinstance(password, str)
        and len(password) >= 6
        and re.search(r"[A-Z]", password)
        and re.search(r"[^A-Za-z0-9]", password)
    ):
        raise error_type(PASSWORD_RULE_MESSAGE)


def hash_password(password: str) -> str:
    # simple project-level hashing helper used before storing passwords
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def password_matches(password: str, password_hash: str) -> bool:
    # compare by hashing the incoming password and checking against the saved hash
    return hash_password(password) == password_hash
