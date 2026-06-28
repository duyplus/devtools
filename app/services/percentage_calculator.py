from decimal import Decimal, InvalidOperation


class PercentageError(ValueError):
    def __init__(self, key, **params):
        self.key = key
        self.params = params
        super().__init__(key)


def calculate_percentage(form):
    mode = form.get("mode", "of")

    if mode == "of":
        percent = _number(form.get("percent"), "percentage.label.percent")
        value = _number(form.get("value"), "percentage.label.value")
        return _fmt(value * percent / Decimal("100"))

    if mode == "ratio":
        value = _number(form.get("value"), "percentage.label.value")
        base = _number(form.get("base"), "percentage.label.base")
        _nonzero(base, "percentage.label.base")
        return f"{_fmt(value / base * Decimal('100'))}%"

    if mode == "change":
        percent = _number(form.get("percent"), "percentage.label.percent")
        value = _number(form.get("value"), "percentage.label.value")
        direction = form.get("direction", "increase")
        factor = Decimal("1") + percent / Decimal("100")
        if direction == "decrease":
            factor = Decimal("1") - percent / Decimal("100")
        elif direction != "increase":
            raise PercentageError("percentage.error.direction")
        return _fmt(value * factor)

    if mode == "total":
        percent = _number(form.get("percent"), "percentage.label.percent")
        value = _number(form.get("value"), "percentage.label.part")
        _nonzero(percent, "percentage.label.percent")
        return _fmt(value * Decimal("100") / percent)

    raise PercentageError("percentage.error.mode")


def _number(raw, label):
    try:
        value = Decimal(str(raw).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise PercentageError("percentage.error.number", label=label) from exc
    if not value.is_finite():
        raise PercentageError("percentage.error.finite", label=label)
    return value


def _nonzero(value, label):
    if value == 0:
        raise PercentageError("percentage.error.zero", label=label)


def _fmt(value):
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return str(normalized.quantize(Decimal("1")))
    return format(normalized, "f").rstrip("0").rstrip(".")
