from dataclasses import dataclass


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    category: str
    endpoint: str
    icon: str
    order: int


TOOLS = sorted(
    (
        ToolDefinition(
            id="icons",
            name="Icon Studio",
            description="Generate favicon packs and custom ICO files.",
            category="Images",
            endpoint="icon_converter.index",
            icon="image",
            order=10,
        ),
        ToolDefinition(
            id="delimiter",
            name="Delimiter Converter",
            description="Convert lists between lines, commas, pipes, spaces, and custom separators.",
            category="Text",
            endpoint="comma_delimiter.index",
            icon="list-filter",
            order=20,
        ),
        ToolDefinition(
            id="text_diff",
            name="Text Diff",
            description="Compare two text blocks, highlight changes, and merge selected hunks.",
            category="Text",
            endpoint="text_diff.index",
            icon="git-compare",
            order=25,
        ),
        ToolDefinition(
            id="percentage",
            name="Percentage Calculator",
            description="Calculate percentage, ratio, increase, decrease, and total.",
            category="Math",
            endpoint="percentage_calculator.index",
            icon="percent",
            order=30,
        ),
        ToolDefinition(
            id="base64",
            name="Base64 Encoder/Decoder",
            description="Encode and decode UTF-8 text with Base64.",
            category="Text",
            endpoint="base64_converter.index",
            icon="binary",
            order=40,
        ),
        ToolDefinition(
            id="javascript",
            name="JavaScript Obfuscator/Deobfuscator",
            description="Obfuscate JavaScript and decode supported obfuscated wrappers.",
            category="Code",
            endpoint="js_obfuscator.index",
            icon="braces",
            order=50,
        ),
        ToolDefinition(
            id="password",
            name="Password Generator",
            description="Generate secure random passwords with custom options.",
            category="Security",
            endpoint="password_generator.index",
            icon="key-round",
            order=60,
        ),
        ToolDefinition(
            id="qr",
            name="QR Generator",
            description="Create custom QR codes for URLs, text, contact details, WiFi, and more.",
            category="Images",
            endpoint="qr_generator.index",
            icon="qr-code",
            order=70,
        ),
    ),
    key=lambda tool: tool.order,
)
