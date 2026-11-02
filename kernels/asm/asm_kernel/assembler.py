"""Thin wrapper around NASM that maps error lines back to the student's cell."""

import os
import re
import subprocess
import tempfile

_ERROR_RE = re.compile(r"^[^:]*:(\d+): (?:error|fatal): (.*)$")


class AsmError(Exception):
    """Assembly failed; the message is ready to show to a student."""


def assemble(source: str, org: int, prelude: str = "") -> bytes:
    """Assemble `source` as flat 64-bit code loaded at address `org`.

    `prelude` is inserted before the source (defines, directives). Error
    line numbers are reported relative to `source`.
    """
    header = f"BITS 64\nORG {org:#x}\n{prelude}"
    if header and not header.endswith("\n"):
        header += "\n"
    offset = header.count("\n")

    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "cell.asm")
        out_path = os.path.join(tmp, "cell.bin")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(header + source + "\n")
        proc = subprocess.run(
            ["nasm", "-f", "bin", "-o", out_path, src_path],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise AsmError(_format_errors(proc.stderr, offset))
        with open(out_path, "rb") as f:
            return f.read()


def _format_errors(stderr: str, offset: int) -> str:
    messages = []
    for raw in stderr.splitlines():
        match = _ERROR_RE.match(raw)
        if not match:
            continue
        line, text = int(match.group(1)) - offset, match.group(2)
        if line > 0:
            messages.append(f"line {line}: {text}")
        else:
            messages.append(text)
    return "\n".join(messages) or stderr.strip() or "assembly failed"
