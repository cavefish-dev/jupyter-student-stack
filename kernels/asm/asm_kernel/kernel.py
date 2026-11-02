"""Jupyter kernel: each cell runs on the same emulated x86-64 CPU."""

from ipykernel.kernelbase import Kernel

from . import __version__, render
from .assembler import AsmError
from .machine import Machine, Result

HELP = """Step-by-step x86-64 assembly (NASM, Intel syntax).

Each cell runs on the same CPU, so registers and memory carry over.
Use the DATA area for memory: mov qword [DATA], 42

Magics (the whole cell):
  %regs                 show all registers
  %mem <addr> [len]     dump memory, e.g. %mem DATA 32, %mem rsp 16
  %reset                start again with a fresh CPU
  %%program             run a complete program (sections, _start, syscalls)
  %help                 this message
"""


class AsmKernel(Kernel):
    implementation = "asm_kernel"
    implementation_version = __version__
    language = "nasm"
    language_version = "x86-64"
    language_info = {
        "name": "nasm",
        "mimetype": "text/x-nasm",
        "file_extension": ".asm",
        "codemirror_mode": "gas",
        "pygments_lexer": "nasm",
    }
    banner = "x86-64 Assembly (NASM) - step-by-step emulated CPU"
    help_links = [{"text": "NASM manual", "url": "https://www.nasm.us/doc/"}]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.machine = Machine()

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False, *, cell_meta=None, cell_id=None):
        first, _, rest = code.strip().partition("\n")
        words = first.split()
        command = words[0] if words else ""
        try:
            if command == "%%program":
                return self._show(self.machine.run_program(rest), silent)
            if command == "%reset":
                self.machine.reset()
                self._stream("CPU reset: registers, memory and definitions are cleared.\n")
                return self._show(Result(registers=self.machine.registers()), silent)
            if command == "%regs":
                return self._show(Result(registers=self.machine.registers()), silent)
            if command == "%mem":
                return self._mem(words[1:], silent)
            if command == "%help":
                self._stream(HELP)
                return self._ok()
            return self._show(self.machine.run_cell(code), silent)
        except AsmError as e:
            return self._error("AssemblyError", str(e))
        except ValueError as e:
            return self._error("Error", str(e))

    def _mem(self, args, silent):
        if not args or len(args) > 2:
            raise ValueError("Usage: %mem <address> [length], e.g. %mem DATA 32")
        length = int(args[1], 0) if len(args) == 2 else 64
        if not 0 < length <= 4096:
            raise ValueError("Length must be between 1 and 4096 bytes.")
        address = self.machine.resolve(args[0])
        data = self.machine.mem(args[0], length)
        if not silent:
            self._display(*render.hexdump(address, data))
        return self._ok()

    def _show(self, result: Result, silent):
        if not silent:
            if result.stdout:
                self._stream(result.stdout)
            if result.exit_code is not None:
                self._stream(f"\n[program exited with code {result.exit_code}]\n")
            self._display(*render.registers(result.registers, result.changed))
        if result.error:
            return self._error("CPUError", result.error)
        return self._ok()

    def _display(self, html, text):
        self.send_response(self.iopub_socket, "display_data", {
            "data": {"text/html": html, "text/plain": text},
            "metadata": {},
        })

    def _stream(self, text, name="stdout"):
        self.send_response(self.iopub_socket, "stream", {"name": name, "text": text})

    def _ok(self):
        return {"status": "ok", "execution_count": self.execution_count,
                "payload": [], "user_expressions": {}}

    def _error(self, ename, evalue):
        content = {"ename": ename, "evalue": evalue, "traceback": [f"{ename}: {evalue}"]}
        self.send_response(self.iopub_socket, "error", content)
        return {"status": "error", "execution_count": self.execution_count, **content}
