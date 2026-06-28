import secrets
import string
from dataclasses import dataclass


class PasswordError(ValueError):
    def __init__(self, key, **params):
        self.key = key
        self.params = params
        super().__init__(key)


@dataclass(frozen=True)
class PasswordOptions:
    length: int = 16
    count: int = 1
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True


SYMBOLS = "!@#$%^&*"


def generate_passwords(options):
    length = _bounded_int(options.length, "password.length", 4, 128)
    count = _bounded_int(options.count, "password.count", 1, 50)
    groups = _groups(options)
    if not groups:
        raise PasswordError("password.error.no_types")
    if length < len(groups):
        raise PasswordError("password.error.too_short")
    return [_generate_one(length, groups) for _ in range(count)]


def _bounded_int(value, label, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise PasswordError("password.error.number", label=label) from exc
    if number < minimum or number > maximum:
        raise PasswordError("password.error.range", label=label, minimum=minimum, maximum=maximum)
    return number


def _groups(options):
    groups = []
    if options.lowercase:
        groups.append(string.ascii_lowercase)
    if options.uppercase:
        groups.append(string.ascii_uppercase)
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
