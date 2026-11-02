"""Install the kernelspec: python -m asm_kernel.install [--user | --sys-prefix | --prefix DIR]"""

import argparse
import json
import os
import sys
import tempfile

from jupyter_client.kernelspec import KernelSpecManager

KERNEL_JSON = {
    "argv": [sys.executable, "-m", "asm_kernel", "-f", "{connection_file}"],
    "display_name": "x86-64 Assembly (NASM)",
    "language": "nasm",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--user", action="store_true", help="install for the current user")
    group.add_argument("--sys-prefix", action="store_true", help="install into sys.prefix")
    group.add_argument("--prefix", help="install into this prefix")
    args = parser.parse_args(argv)

    prefix = sys.prefix if args.sys_prefix else args.prefix
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "kernel.json"), "w") as f:
            json.dump(KERNEL_JSON, f, indent=2)
        dest = KernelSpecManager().install_kernel_spec(
            tmp, "asm", user=args.user, prefix=prefix, replace=True
        )
    print(f"Installed x86-64 Assembly kernel in {dest}")


if __name__ == "__main__":
    main()
