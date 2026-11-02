#!/bin/bash
# x86-64 assembly: NASM + this repo's step-by-step kernel (source mounted at /tmp/asm-kernel)
set -euxo pipefail

apt-get update
apt-get install -y --no-install-recommends nasm
rm -rf /var/lib/apt/lists/*

pip install --no-cache-dir /tmp/asm-kernel
python -m asm_kernel.install --sys-prefix
