"""Turn machine state into notebook output (HTML with a plain-text fallback)."""

from html import escape
from typing import Dict, Iterable, Set, Tuple

from .machine import FLAG_BITS, decode_flags

_GENERAL = [
    "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
    "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15",
]

_STYLE = (
    "<style>"
    ".asmk{border-collapse:collapse;font-family:var(--jp-code-font-family,monospace);font-size:12px}"
    ".asmk td,.asmk th{padding:1px 8px;text-align:right}"
    ".asmk th{text-align:left}"
    ".asmk .chg{background:rgba(255,196,0,.35);font-weight:bold}"
    ".asmk .gap{width:24px}"
    ".asmk-flags span{display:inline-block;margin-right:10px;font-family:var(--jp-code-font-family,monospace)}"
    ".asmk-flags .on{font-weight:bold}"
    "</style>"
)


def signed(value: int) -> int:
    return value - (1 << 64) if value & (1 << 63) else value


def registers(regs: Dict[str, int], changed: Set[str] = frozenset()) -> Tuple[str, str]:
    """Return (html, text) for the register table; `changed` registers are highlighted."""
    half = len(_GENERAL) // 2
    rows_html, rows_text = [], []
    for left, right in zip(_GENERAL[:half], _GENERAL[half:]):
        cells, texts = [], []
        for name in (left, right):
            value = regs[name]
            cls = ' class="chg"' if name in changed else ""
            cells.append(
                f"<th{cls}>{name.upper()}</th><td{cls}>{value:#018x}</td><td{cls}>{signed(value)}</td>"
            )
            mark = "*" if name in changed else " "
            texts.append(f"{mark}{name.upper():<4} {value:#018x} {signed(value):>20}")
        rows_html.append("<tr>" + '<td class="gap"></td>'.join(cells) + "</tr>")
        rows_text.append("   ".join(texts))

    rip_cls = ' class="chg"' if "rip" in changed else ""
    rows_html.append(
        f'<tr><th{rip_cls}>RIP</th><td{rip_cls}>{regs["rip"]:#018x}</td><td></td></tr>'
    )
    rows_text.append(f' RIP  {regs["rip"]:#018x}')

    flags = decode_flags(regs["rflags"])
    flags_html = "".join(
        f'<span class="{"on" if flags[f] else ""}">{f}={flags[f]}</span>' for f in FLAG_BITS
    )
    flags_text = "  ".join(f"{f}={flags[f]}" for f in FLAG_BITS)

    html = (
        _STYLE
        + '<table class="asmk"><tr><th>Reg</th><th>Hex</th><th>Decimal</th><td class="gap"></td>'
        + "<th>Reg</th><th>Hex</th><th>Decimal</th></tr>"
        + "".join(rows_html)
        + f'</table><div class="asmk-flags">Flags: {flags_html}</div>'
    )
    text = "\n".join(rows_text) + "\nFlags: " + flags_text
    if changed - {"rip", "rflags"}:
        text += "\n(* = changed by this cell)"
    return html, text


def hexdump(address: int, data: bytes) -> Tuple[str, str]:
    """Return (html, text) for a classic 16-bytes-per-row hex dump."""
    lines = list(_hexdump_lines(address, data))
    text = "\n".join(lines)
    return f'<pre class="asmk">{escape(text)}</pre>', text


def _hexdump_lines(address: int, data: bytes) -> Iterable[str]:
    for offset in range(0, len(data), 16):
        chunk = data[offset:offset + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk).ljust(47)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        yield f"{address + offset:#010x}  {hex_part}  {ascii_part}"
