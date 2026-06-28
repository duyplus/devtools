from dataclasses import dataclass
import re


class DelimiterError(ValueError):
    def __init__(self, key):
        self.key = key
        self.params = {}
        super().__init__(key)


@dataclass(frozen=True)
class DelimiterOptions:
    input_delimiter: str = "newline"
    input_custom: str = ""
    output_delimiter: str = "comma"
    output_custom: str = ""
    trim: bool = True
    remove_blank: bool = True
    dedupe: bool = False
    quote: str = "none"
    prefix: str = ""
    suffix: str = ""
    interval: int = 0


DELIMITERS = {
    "newline": "\n",
    "comma": ",",
    "semicolon": ";",
    "pipe": "|",
    "spaces": " ",
}


def convert_text(text, options):
    items = _split(text, options.input_delimiter, options.input_custom)

    if options.trim:
        items = [item.strip() for item in items]
    if options.remove_blank:
        items = [item for item in items if item != ""]
    if options.dedupe:
        items = _dedupe(items)

    quote = _quote(options.quote)
    items = [f"{options.prefix}{quote}{item}{quote}{options.suffix}" for item in items]

    output_delimiter = _delimiter(options.output_delimiter, options.output_custom)
    return _join(items, output_delimiter, options.interval)


def _split(text, delimiter_name, custom):
    delimiter = _delimiter(delimiter_name, custom)
    if delimiter_name == "newline":
        return text.splitlines()
    if delimiter_name == "spaces":
        return re.split(r"\s+", text)
    return text.split(delimiter)


def _delimiter(name, custom):
    if name == "custom":
        if custom == "":
            raise DelimiterError("delimiter.error.custom_empty")
        return custom
    if name not in DELIMITERS:
        raise DelimiterError("delimiter.error.unsupported_delimiter")
    return DELIMITERS[name]


def _quote(name):
    if name == "none":
        return ""
    if name == "single":
        return "'"
    if name == "double":
        return '"'
    raise DelimiterError("delimiter.error.unsupported_quote")


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _join(items, delimiter, interval):
    if interval < 0:
        raise DelimiterError("delimiter.error.interval")
    if interval == 0:
        return delimiter.join(items)

    chunks = [items[index : index + interval] for index in range(0, len(items), interval)]
    return "\n".join(delimiter.join(chunk) for chunk in chunks)
