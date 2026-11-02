#!/bin/bash
# C: gcc + jupyter-c-kernel (each cell is compiled as a whole program)
set -euxo pipefail

apt-get update
apt-get install -y --no-install-recommends gcc g++ make libc6-dev
rm -rf /var/lib/apt/lists/*

pip install --no-cache-dir jupyter-c-kernel
install_c_kernel --sys-prefix
