import secrets
import string
from dataclasses import dataclass


class PasswordError(ValueError):
    pass


@dataclass(frozen=True)
class PasswordOptions:
    length: int = 16
    count: int = 1
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    symbols: bool = True


SYMBOLS = "!@#$%^&*"


def generate_passwords(options):
    length = _bounded_int(options.length, "Password length", 4, 128)
    count = _bounded_int(options.count, "Password count", 1, 50)
    groups = _groups(options)
    if not groups:
        raise PasswordError("Select at least one character type.")
    if length < len(groups):
        raise PasswordError("Password length is too short for the selected character types.")
    return [_generate_one(length, groups) for _ in range(count)]


def _bounded_int(value, label, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise PasswordError(f"{label} must be a number.") from exc
    if number < minimum or number > maximum:
        raise PasswordError(f"{label} must be between {minimum} and {maximum}.")
    return number


def _groups(options):
    groups = []
    if options.uppercase:
        groups.append(string.ascii_uppercase)
    if options.lowercase:
        groups.append(string.ascii_lowercase)
    if options.digits:
        groups.append(string.digits)
    if options.symbols:
        groups.append(SYMBOLS)
    return groups


def _generate_one(length, groups):
    password = [secrets.choice(group) for group in groups]
    pool = "".join(groups)
    password.extend(secrets.choice(pool) for _ in range(length - len(password)))
    secrets.SystemRandom().shuffle(password)
    return "".join(password)
