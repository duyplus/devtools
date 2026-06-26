from decimal import Decimal, InvalidOperation


class PercentageError(ValueError):
    pass


def calculate_percentage(form):
    mode = form.get("mode", "of")

    if mode == "of":
        percent = _number(form.get("percent"), "Percent")
        value = _number(form.get("value"), "Value")
        return _fmt(value * percent / Decimal("100"))

    if mode == "ratio":
        value = _number(form.get("value"), "Value")
        base = _number(form.get("base"), "Base")
        _nonzero(base, "Base")
        return f"{_fmt(value / base * Decimal('100'))}%"

    if mode == "change":
        percent = _number(form.get("percent"), "Percent")
        value = _number(form.get("value"), "Value")
        direction = form.get("direction", "increase")
        factor = Decimal("1") + percent / Decimal("100")
        if direction == "decrease":
            factor = Decimal("1") - percent / Decimal("100")
        elif direction != "increase":
            raise PercentageError("Unsupported change direction.")
        return _fmt(value * factor)

    if mode == "total":
        percent = _number(form.get("percent"), "Percent")
        value = _number(form.get("value"), "Part")
        _nonzero(percent, "Percent")
        return _fmt(value * Decimal("100") / percent)

    raise PercentageError("Unsupported percentage mode.")


def _number(raw, label):
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise PercentageError(f"{label} must be a number.") from exc
    if not value.is_finite():
        raise PercentageError(f"{label} must be finite.")
    return value


def _nonzero(value, label):
    if value == 0:
        raise PercentageError(f"{label} cannot be zero.")


def _fmt(value):
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f").rstrip("0").rstrip(".")
