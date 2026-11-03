import pytest

from asm_kernel.assembler import AsmError
from asm_kernel.machine import DATA, DATA_SIZE, STACK_TOP, Machine


@pytest.fixture
def m():
    return Machine()


def test_registers_persist_between_cells(m):
    m.run_cell("mov rax, 5")
    r = m.run_cell("add rax, 3")
    assert r.registers["rax"] == 8
    assert "rax" in r.changed


def test_changed_registers_only(m):
    r = m.run_cell("mov rbx, 1\nmov rcx, 2")
    assert {"rbx", "rcx"} <= r.changed
    assert "rdx" not in r.changed


def test_flags_after_cmp(m):
    r = m.run_cell("mov rax, 3\ncmp rax, 3")
    assert r.flags["ZF"] == 1
    r = m.run_cell("cmp rax, 4")
    assert r.flags["ZF"] == 0
    assert r.flags["SF"] == 1
    assert r.flags["CF"] == 1


def test_loop_within_cell(m):
    r = m.run_cell(
        """
        mov rcx, 5
        xor rax, rax
    again:
        add rax, rcx
        dec rcx
        jnz again
        """
    )
    assert r.registers["rax"] == 15


def test_stack_push_pop(m):
    r = m.run_cell("mov rax, 42\npush rax")
    assert r.registers["rsp"] == STACK_TOP - 8
    r = m.run_cell("pop rbx")
    assert r.registers["rbx"] == 42


def test_data_region_and_mem(m):
    m.run_cell("mov rax, 0x1122334455667788\nmov [DATA], rax")
    assert m.mem("DATA", 8) == bytes.fromhex("8877665544332211")
    assert m.mem("DATA+4", 4) == bytes.fromhex("44332211")
    assert DATA_SIZE == 0x10000


def test_mem_by_register(m):
    m.run_cell("mov rax, 7\npush rax")
    assert m.mem("rsp", 8) == (7).to_bytes(8, "little")


def test_defines_persist(m):
    m.run_cell("%define COUNT 10\nLIMIT equ 20")
    r = m.run_cell("mov rax, COUNT\nmov rbx, LIMIT")
    assert r.registers["rax"] == 10
    assert r.registers["rbx"] == 20
    # redefining an equ must not break later cells
    m.run_cell("LIMIT equ 30")
    r = m.run_cell("mov rbx, LIMIT")
    assert r.registers["rbx"] == 30


def test_reset(m):
    m.run_cell("mov rax, 99\nmov qword [DATA], 1")
    m.reset()
    assert m.registers()["rax"] == 0
    assert m.mem("DATA", 8) == bytes(8)


def test_error_line_number(m):
    with pytest.raises(AsmError) as e:
        m.run_cell("mov rax, 1\nmov rax, 2\nmvo rbx, 3")
    assert "line 3" in str(e.value)


def test_data_rejected_incremental(m):
    with pytest.raises(AsmError) as e:
        m.run_cell('msg: db "hi", 0')
    assert "%%program" in str(e.value)


def test_infinite_loop_limit(m):
    r = m.run_cell("spin: jmp spin")
    assert r.error and "limit" in r.error.lower()
    # kernel keeps working afterwards
    r = m.run_cell("mov rax, 1")
    assert r.error is None and r.registers["rax"] == 1


def test_unmapped_access(m):
    r = m.run_cell("mov rax, [0x10]")
    assert r.error and "memory" in r.error.lower()
    assert "0x" in r.error


def test_write_syscall_incremental(m):
    r = m.run_cell(
        """
        mov byte [DATA], 'H'
        mov byte [DATA+1], 'i'
        mov rax, 1
        mov rdi, 1
        mov rsi, DATA
        mov rdx, 2
        syscall
        """
    )
    assert r.stdout == "Hi"
    assert r.registers["rax"] == 2


HELLO = """
section .data
    msg db "Hello, world!", 10
    len equ $ - msg

section .text
global _start
_start:
    mov rax, 1
    mov rdi, 1
    mov rsi, msg
    mov rdx, len
    syscall
    mov rax, 60
    mov rdi, 7
    syscall
"""


def test_program_hello(m):
    r = m.run_program(HELLO)
    assert r.error is None
    assert r.stdout == "Hello, world!\n"
    assert r.exit_code == 7


def test_program_bss(m):
    r = m.run_program(
        """
section .bss
    buf resq 1
section .text
_start:
    mov qword [buf], 5
    mov rax, [buf]
    mov rdi, rax
    mov rax, 60
    syscall
"""
    )
    assert r.exit_code == 5


def test_program_without_exit(m):
    r = m.run_program("section .text\n_start:\n    mov rax, 1\n")
    assert r.error and "exit" in r.error


def test_program_without_start(m):
    with pytest.raises(AsmError) as e:
        m.run_program("section .text\n    mov rax, 1\n")
    assert "_start" in str(e.value)


def test_program_error_line_number(m):
    with pytest.raises(AsmError) as e:
        m.run_program("section .text\n_start:\n    movv rax, 1\n")
    assert "line 3" in str(e.value)


def test_unsupported_syscall(m):
    r = m.run_cell("mov rax, 57\nsyscall")
    assert r.error and "57" in r.error
