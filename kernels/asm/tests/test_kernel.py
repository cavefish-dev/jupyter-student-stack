"""End-to-end tests through a real kernel process (needs the kernelspec installed)."""

import pytest
from jupyter_client.manager import start_new_kernel

from asm_kernel import render


@pytest.fixture(scope="module")
def kc():
    km, client = start_new_kernel(kernel_name="asm")
    yield client
    client.stop_channels()
    km.shutdown_kernel(now=True)


def run(kc, code):
    outputs = []
    reply = kc.execute_interactive(code, output_hook=lambda msg: outputs.append(msg), timeout=30)
    return reply["content"], outputs


def texts(outputs):
    result = []
    for msg in outputs:
        content = msg["content"]
        if msg["msg_type"] == "stream":
            result.append(content["text"])
        elif msg["msg_type"] == "display_data":
            result.append(content["data"]["text/plain"])
        elif msg["msg_type"] == "error":
            result.append(content["evalue"])
    return "\n".join(result)


def test_state_carries_over_and_highlights(kc):
    run(kc, "%reset")
    run(kc, "mov rax, 5")
    reply, outputs = run(kc, "add rax, 3")
    assert reply["status"] == "ok"
    out = texts(outputs)
    assert "*RAX" in out and "0x0000000000000008" in out


def test_mem_magic(kc):
    run(kc, "%reset")
    run(kc, "mov byte [DATA], 'A'")
    reply, outputs = run(kc, "%mem DATA 16")
    assert reply["status"] == "ok"
    assert "0x00600000  41 00" in texts(outputs)


def test_program_magic(kc):
    reply, outputs = run(kc, '%%program\nsection .data\nmsg db "Hi", 10\nsection .text\n'
                             'global _start\n_start:\nmov rax, 1\nmov rdi, 1\nmov rsi, msg\n'
                             'mov rdx, 3\nsyscall\nmov rax, 60\nxor rdi, rdi\nsyscall\n')
    assert reply["status"] == "ok"
    out = texts(outputs)
    assert "Hi\n" in out and "exited with code 0" in out


def test_assembly_error_is_reported(kc):
    reply, outputs = run(kc, "mov rax, 1\nfoo rax")
    assert reply["status"] == "error"
    assert reply["ename"] == "AssemblyError"
    assert "line 2" in reply["evalue"]


def test_bad_mem_usage(kc):
    reply, _ = run(kc, "%mem")
    assert reply["status"] == "error" and "Usage" in reply["evalue"]


def test_hexdump_format():
    _, text = render.hexdump(0x600000, b"Hello\x00")
    assert text == "0x00600000  48 65 6c 6c 6f 00" + " " * 30 + "  Hello."
