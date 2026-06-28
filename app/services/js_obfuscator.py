import base64
import binascii
import re


class JavascriptToolError(ValueError):
    def __init__(self, key):
        self.key = key
        self.params = {}
        super().__init__(key)


_APP_V1_RE = re.compile(
    r"const\s+d\s*=\s*([\"'])(?P<data>[A-Za-z0-9+/=\s]+)\1.*TextDecoder\(\)\.decode",
    re.DOTALL,
)
_ATOB_RE = re.compile(
    r"eval\s*\(\s*atob\s*\(\s*([\"'])(?P<data>[A-Za-z0-9+/=\s]+)\1\s*\)\s*\)",
    re.DOTALL,
)
_V2_MARKER_RE = re.compile(r"devtools-js-obfuscator:v2;enc=(?P<encoding>[a-z0-9-]+)")
_V2_DIRECT_RE = re.compile(r"const\s+d\s*=\s*\"(?P<data>[A-Za-z0-9+/=\s]+)\"")
_V2_ARRAY_RE = re.compile(r"const\s+p\s*=\s*\[(?P<items>[^\]]*)\]")
_V2_KEY_RE = re.compile(r"const\s+k\s*=\s*\"(?P<key>[^\"]+)\"")


DEFAULT_OPTIONS = {
    "compact": True,
    "string_array": True,
    "debug_protection": False,
    "numbers_to_expressions": False,
    "control_flow_flattening": False,
    "self_defending": False,
    "simplify": True,
    "split_strings": False,
    "string_array_threshold": "0.75",
    "control_flow_threshold": "0.75",
    "split_strings_chunk_length": "10",
    "string_array_encoding": "none",
}


def obfuscate_javascript(source, options=None):
    options = _normalize_options(options or {})
    encoded_payload = _encode_payload(source, options["string_array_encoding"])
    payload_js = _payload_js(encoded_payload, options)
    decoder_js = _decoder_js(options)
    body = payload_js + decoder_js

    if options["debug_protection"]:
        body = 'setInterval(()=>{debugger;},4000);' + body
    if options["self_defending"]:
        body = 'if(!Function.prototype.toString)throw new Error("tamper");' + body
    if options["control_flow_flattening"]:
        body = "let s=0;while(true){switch(s){case 0:" + body + "return;}}"

    output = f"/* devtools-js-obfuscator:v2;enc={options['string_array_encoding']} */(()=>{{{body}}})();"
    if not options["compact"]:
        return _pretty_output(output)
    return output


def deobfuscate_javascript(source):
    decoded = _decode_v2_wrapper(source)
    if decoded is not None:
        return decoded

    decoded = _decode_known_base64_wrapper(source)
    if decoded is not None:
        return decoded

    decoded = _decode_js_escapes(source)
    if decoded != source:
        return decoded

    raise JavascriptToolError("javascript.error.pattern")


def _normalize_options(options):
    normalized = DEFAULT_OPTIONS.copy()
    normalized.update(options)

    for key in (
        "compact",
        "string_array",
        "debug_protection",
        "numbers_to_expressions",
        "control_flow_flattening",
        "self_defending",
        "simplify",
        "split_strings",
    ):
        normalized[key] = bool(normalized.get(key))

    encoding = normalized.get("string_array_encoding") or "none"
    if encoding not in {"none", "base64", "rc4"}:
        raise JavascriptToolError("javascript.error.encoding")
    normalized["string_array_encoding"] = encoding
    normalized["split_strings_chunk_length"] = _positive_int(
        normalized.get("split_strings_chunk_length"),
        10,
    )
    return normalized


def _positive_int(value, fallback):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(parsed, 1)


def _encode_payload(source, encoding):
    source_bytes = source.encode("utf-8")
    if encoding == "base64":
        source_bytes = base64.b64encode(source_bytes)
    if encoding == "rc4":
        source_bytes = _rc4(source_bytes, b"devtools")
    return base64.b64encode(source_bytes).decode("ascii")


def _payload_js(encoded_payload, options):
    if not options["string_array"] and not options["split_strings"]:
        return f'const d="{encoded_payload}";'

    chunk_length = options["split_strings_chunk_length"] if options["split_strings"] else 32
    chunks = [encoded_payload[index : index + chunk_length] for index in range(0, len(encoded_payload), chunk_length)]
    return "const p=[" + ",".join(f'"{chunk}"' for chunk in chunks) + "];const d=p.join('');"


def _decoder_js(options):
    codepoint = "charCodeAt(1-1)" if options["numbers_to_expressions"] else "charCodeAt(0)"
    binary = 'typeof atob==="function"?atob(d):Buffer.from(d,"base64").toString("binary")'
    bytes_js = f"Uint8Array.from(b,c=>c.{codepoint})"
    if options["string_array_encoding"] == "base64":
        return (
            f"const b={binary};const i=typeof atob==='function'?atob(b):Buffer.from(b,'base64').toString('binary');"
            f"const a=Uint8Array.from(i,c=>c.{codepoint});(0,eval)(new TextDecoder().decode(a));"
        )
    if options["string_array_encoding"] == "rc4":
        return (
            f"const k=\"devtools\";const b={binary};const a={bytes_js};"
            "for(let i=0,j=0,s=Array.from({length:256},(_,x)=>x);i<256;i++){j=(j+s[i]+k.charCodeAt(i%k.length))&255;[s[i],s[j]]=[s[j],s[i]];}"
            "for(let i=0,j=0,y=0;y<a.length;y++){i=(i+1)&255;j=(j+s[i])&255;[s[i],s[j]]=[s[j],s[i]];a[y]^=s[(s[i]+s[j])&255];}"
            "(0,eval)(new TextDecoder().decode(a));"
        )
    return f"const b={binary};const a={bytes_js};(0,eval)(new TextDecoder().decode(a));"


def _pretty_output(output):
    return (
        output.replace("*/", "*/\n")
        .replace("(()=>{", "(()=>{\n  ")
        .replace(";const ", ";\n  const ")
        .replace(";let ", ";\n  let ")
        .replace(";if", ";\n  if")
        .replace(";for", ";\n  for")
        .replace(";return", ";\n  return")
        .replace(";})();", ";\n})();")
    )


def _decode_v2_wrapper(source):
    marker = _V2_MARKER_RE.search(source)
    if not marker:
        return None

    payload = _extract_v2_payload(source)
    decoded = _decode_base64_bytes(payload)
    encoding = marker.group("encoding")

    if encoding == "base64":
        decoded = _decode_base64_bytes(decoded.decode("ascii"))
    elif encoding == "rc4":
        key = _V2_KEY_RE.search(source)
        decoded = _rc4(decoded, (key.group("key") if key else "devtools").encode("utf-8"))
    elif encoding != "none":
        raise JavascriptToolError("javascript.error.encoding")

    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise JavascriptToolError("javascript.error.invalid_utf8") from exc


def _extract_v2_payload(source):
    direct = _V2_DIRECT_RE.search(source)
    if direct:
        return direct.group("data")

    array = _V2_ARRAY_RE.search(source)
    if array:
        return "".join(re.findall(r'"([^"]*)"', array.group("items")))

    raise JavascriptToolError("javascript.error.pattern")


def _decode_known_base64_wrapper(source):
    for pattern in (_APP_V1_RE, _ATOB_RE):
        match = pattern.search(source)
        if match:
            return _decode_base64_text(match.group("data"))
    return None


def _decode_base64_bytes(value):
    normalized = re.sub(r"\s+", "", value)
    try:
        return base64.b64decode(normalized.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise JavascriptToolError("javascript.error.invalid_base64") from exc


def _decode_base64_text(value):
    decoded = _decode_base64_bytes(value)
    try:
        return decoded.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise JavascriptToolError("javascript.error.invalid_utf8") from exc


def _decode_js_escapes(source):
    source = re.sub(
        r"\\x([0-9a-fA-F]{2})",
        lambda match: chr(int(match.group(1), 16)),
        source,
    )
    return re.sub(
        r"\\u([0-9a-fA-F]{4})",
        lambda match: chr(int(match.group(1), 16)),
        source,
    )


def _rc4(data, key):
    state = list(range(256))
    key_bytes = list(key)
    index = 0
    for counter in range(256):
        index = (index + state[counter] + key_bytes[counter % len(key_bytes)]) & 255
        state[counter], state[index] = state[index], state[counter]

    first = second = 0
    output = bytearray()
    for byte in data:
        first = (first + 1) & 255
        second = (second + state[first]) & 255
        state[first], state[second] = state[second], state[first]
        output.append(byte ^ state[(state[first] + state[second]) & 255])
    return bytes(output)
