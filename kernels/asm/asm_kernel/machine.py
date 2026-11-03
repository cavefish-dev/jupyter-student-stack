"""Emulated x86-64 CPU that keeps its state between notebook cells."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from unicorn import (
    UC_ARCH_X86,
    UC_ERR_FETCH_UNMAPPED,
    UC_ERR_INSN_INVALID,
    UC_ERR_READ_UNMAPPED,
    UC_ERR_WRITE_UNMAPPED,
    UC_HOOK_INSN,
    UC_HOOK_MEM_INVALID,
    UC_MODE_64,
    Uc,
    UcError,
)
from unicorn import x86_const as x86

from .assembler import AsmError, assemble

MiB = 1024 * 1024

CODE_BASE = 0x400000  # incremental cells are appended here
CODE_SIZE = MiB
PROGRAM_BASE = 0x500000  # %%program images are loaded here
PROGRAM_SIZE = MiB
DATA = 0x600000  # scratch memory students can use from any cell
DATA_SIZE = 0x10000
STACK_TOP = 0x80000000
STACK_SIZE = MiB

MAX_INSTRUCTIONS = 1_000_000
TIMEOUT_US = 5_000_000

REGISTERS = {
    "rax": x86.UC_X86_REG_RAX,
    "rbx": x86.UC_X86_REG_RBX,
    "rcx": x86.UC_X86_REG_RCX,
    "rdx": x86.UC_X86_REG_RDX,
    "rsi": x86.UC_X86_REG_RSI,
    "rdi": x86.UC_X86_REG_RDI,
    "rbp": x86.UC_X86_REG_RBP,
    "rsp": x86.UC_X86_REG_RSP,
    "r8": x86.UC_X86_REG_R8,
    "r9": x86.UC_X86_REG_R9,
    "r10": x86.UC_X86_REG_R10,
    "r11": x86.UC_X86_REG_R11,
    "r12": x86.UC_X86_REG_R12,
    "r13": x86.UC_X86_REG_R13,
    "r14": x86.UC_X86_REG_R14,
    "r15": x86.UC_X86_REG_R15,
    "rip": x86.UC_X86_REG_RIP,
    "rflags": x86.UC_X86_REG_EFLAGS,
}

FLAG_BITS = {"CF": 0, "PF": 2, "AF": 4, "ZF": 6, "SF": 7, "DF": 10, "OF": 11}

SYS_WRITE, SYS_EXIT, SYS_EXIT_GROUP = 1, 60, 231

_DATA_DECL_RE = re.compile(
    r"^\s*(?:[\w.$?@]+:?\s+)?(db|dw|dd|dq|dt|do|dy|dz|resb|resw|resd|resq|rest|reso|resy|resz|incbin)\b"
    r"|^\s*\[?\s*(section|segment)\b",
    re.IGNORECASE,
)
_DEFINE_RE = re.compile(r"^\s*%(?:i?x?define|i?assign)\s+([A-Za-z_.?$][\w.$?@]*)")
_EQU_RE = re.compile(r"^\s*([A-Za-z_.?][\w.$?@]*):?\s+equ\b", re.IGNORECASE)
_GLOBAL_RE = re.compile(r"^\s*(global|extern)\b", re.IGNORECASE)
_ADDR_RE = re.compile(
    r"^\s*([A-Za-z_]\w*|0x[0-9a-fA-F]+|\d+)\s*(?:([+-])\s*(0x[0-9a-fA-F]+|\d+))?\s*$"
)

_PROGRAM_PRELUDE = "section .text\njmp near _start\ndq __asmk_text_end\n"
_PROGRAM_SUFFIX = "\nsection .text\n__asmk_text_end: ud2\n"


@dataclass
class Result:
    registers: Dict[str, int]
    changed: Set[str] = field(default_factory=set)
    stdout: str = ""
    error: Optional[str] = None
    exit_code: Optional[int] = None

    @property
    def flags(self) -> Dict[str, int]:
        return decode_flags(self.registers["rflags"])


def decode_flags(rflags: int) -> Dict[str, int]:
    return {name: (rflags >> bit) & 1 for name, bit in FLAG_BITS.items()}


def _strip_comment(line: str) -> str:
    return line.split(";", 1)[0]


class Machine:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        uc = Uc(UC_ARCH_X86, UC_MODE_64)
        uc.mem_map(CODE_BASE, CODE_SIZE)
        uc.mem_map(PROGRAM_BASE, PROGRAM_SIZE)
        uc.mem_map(DATA, DATA_SIZE)
        uc.mem_map(STACK_TOP - STACK_SIZE, STACK_SIZE)
        uc.reg_write(x86.UC_X86_REG_RSP, STACK_TOP)
        uc.reg_write(x86.UC_X86_REG_RIP, CODE_BASE)
        uc.hook_add(UC_HOOK_INSN, self._on_syscall, None, 1, 0, x86.UC_X86_INS_SYSCALL)
        uc.hook_add(UC_HOOK_MEM_INVALID, self._on_bad_memory)
        self.uc = uc
        self.code_ptr = CODE_BASE
        self.defines: Dict[str, str] = {}  # name -> source line, from earlier cells

    def registers(self) -> Dict[str, int]:
        return {name: self.uc.reg_read(reg) for name, reg in REGISTERS.items()}

    # --- incremental cells -------------------------------------------------

    def run_cell(self, source: str) -> Result:
        lines = source.splitlines()
        for number, line in enumerate(lines, 1):
            if _DATA_DECL_RE.match(_strip_comment(line)):
                raise AsmError(
                    f"line {number}: data declarations and sections only work in a "
                    "%%program cell. In step-by-step cells, store values in the "
                    "DATA area instead, e.g. mov qword [DATA], 42"
                )

        cell_defines = {}
        for line in lines:
            match = _DEFINE_RE.match(line) or _EQU_RE.match(line)
            if match:
                cell_defines[match.group(1)] = line.strip()

        prelude = f"%define DATA {DATA:#x}\n%define DATA_SIZE {DATA_SIZE:#x}\n"
        prelude += "".join(
            line + "\n" for name, line in self.defines.items() if name not in cell_defines
        )
        code = assemble(source, self.code_ptr, prelude)
        self.defines.update(cell_defines)

        before = self.registers()
        if not code:
            return Result(registers=before)
        if self.code_ptr + len(code) > CODE_BASE + CODE_SIZE:
            raise AsmError("The code area is full. Run %reset to start a fresh CPU.")

        start = self.code_ptr
        self.uc.mem_write(start, code)
        self.code_ptr += len(code)
        return self._execute(start, start + len(code), before)

    # --- whole programs ----------------------------------------------------

    def run_program(self, source: str) -> Result:
        source = "\n".join(
            "" if _GLOBAL_RE.match(line) else line for line in source.splitlines()
        )
        try:
            image = assemble(source + _PROGRAM_SUFFIX, PROGRAM_BASE, _PROGRAM_PRELUDE)
        except AsmError as e:
            if "_start" in str(e):
                raise AsmError(
                    "Your program needs a _start: label where execution begins."
                ) from None
            raise

        self.reset()
        self.uc.mem_write(PROGRAM_BASE, image)
        text_end = int.from_bytes(image[5:13], "little")
        before = self.registers()
        result = self._execute(PROGRAM_BASE, text_end, before)
        if result.error is None and result.exit_code is None:
            result.error = (
                "The program reached the end of its code without calling exit "
                "(mov rax, 60 / mov rdi, <code> / syscall)."
            )
        return result

    # --- memory ------------------------------------------------------------

    def resolve(self, expr: str) -> int:
        match = _ADDR_RE.match(expr)
        if not match:
            raise ValueError(f"Can't understand address {expr!r}. Try DATA, rsp or 0x600000.")
        base, sign, offset = match.groups()
        if base.lower() in REGISTERS:
            address = self.uc.reg_read(REGISTERS[base.lower()])
        elif base == "DATA":
            address = DATA
        elif base[0].isdigit():
            address = int(base, 0)
        else:
            raise ValueError(f"Unknown register or name {base!r}.")
        if offset:
            address += int(offset, 0) * (1 if sign == "+" else -1)
        return address

    def mem(self, expr: str, length: int) -> bytes:
        address = self.resolve(expr)
        try:
            return bytes(self.uc.mem_read(address, length))
        except UcError:
            raise ValueError(f"Address {address:#x} (length {length}) is not mapped memory.") from None

    # --- execution ---------------------------------------------------------

    def _execute(self, begin: int, until: int, before: Dict[str, int]) -> Result:
        self._stdout: List[str] = []
        self._error: Optional[str] = None
        self._exit_code: Optional[int] = None
        self._bad_access: Optional[str] = None
        try:
            self.uc.emu_start(begin, until, timeout=TIMEOUT_US, count=MAX_INSTRUCTIONS)
        except UcError as e:
            self._error = self._describe(e)

        after = self.registers()
        if self._error is None and self._exit_code is None and after["rip"] != until:
            self._error = (
                f"Instruction limit reached: stopped after {MAX_INSTRUCTIONS:,} "
                "instructions or 5 seconds. Is there an infinite loop?"
            )
        changed = {name for name in after if after[name] != before[name]}
        return Result(
            registers=after,
            changed=changed,
            stdout="".join(self._stdout),
            error=self._error,
            exit_code=self._exit_code,
        )

    def _describe(self, e: UcError) -> str:
        rip = self.uc.reg_read(x86.UC_X86_REG_RIP)
        if e.errno in (UC_ERR_READ_UNMAPPED, UC_ERR_WRITE_UNMAPPED, UC_ERR_FETCH_UNMAPPED):
            what = self._bad_access or "access unmapped memory"
            return f"Memory error at RIP={rip:#x}: tried to {what}."
        if e.errno == UC_ERR_INSN_INVALID:
            return f"Invalid instruction at RIP={rip:#x}."
        return f"CPU error at RIP={rip:#x}: {e}"

    def _on_bad_memory(self, uc, access, address, size, value, user_data):
        kind = {
            19: "read",  # UC_MEM_READ_UNMAPPED
            20: "write",  # UC_MEM_WRITE_UNMAPPED
            21: "execute",  # UC_MEM_FETCH_UNMAPPED
        }.get(access, "access")
        self._bad_access = f"{kind} unmapped address {address:#x}"
        return False

    def _on_syscall(self, uc, user_data):
        number = uc.reg_read(x86.UC_X86_REG_RAX)
        if number == SYS_WRITE:
            fd = uc.reg_read(x86.UC_X86_REG_RDI)
            buf = uc.reg_read(x86.UC_X86_REG_RSI)
            count = uc.reg_read(x86.UC_X86_REG_RDX)
            if fd in (1, 2):
                try:
                    data = bytes(uc.mem_read(buf, count))
                except UcError:
                    uc.reg_write(x86.UC_X86_REG_RAX, (-14) & (2**64 - 1))  # EFAULT
                    return
                self._stdout.append(data.decode("utf-8", errors="replace"))
                uc.reg_write(x86.UC_X86_REG_RAX, count)
            else:
                uc.reg_write(x86.UC_X86_REG_RAX, (-9) & (2**64 - 1))  # EBADF
        elif number in (SYS_EXIT, SYS_EXIT_GROUP):
            self._exit_code = uc.reg_read(x86.UC_X86_REG_RDI) & 0xFF
            uc.emu_stop()
        else:
            self._error = (
                f"System call {number} is not supported here. "
                "Supported: write (1), exit (60), exit_group (231)."
            )
            uc.emu_stop()
