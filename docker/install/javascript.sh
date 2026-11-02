#!/bin/bash
# JavaScript/TypeScript: Deno kernel + TypeScript language server
set -euxo pipefail

cd /tmp
wget -q "https://github.com/denoland/deno/releases/latest/download/deno-$(uname -m)-unknown-linux-gnu.zip" -O deno.zip
unzip -q deno.zip -d /usr/local/bin
rm deno.zip

# `deno jupyter --install` writes to $HOME; move the kernelspec to the system location.
deno jupyter --install --force
mv "${HOME}/.local/share/jupyter/kernels/deno" "${CONDA_DIR}/share/jupyter/kernels/deno"
rm -rf "${HOME}/.local/share/jupyter" "${HOME}/.cache/deno"

npm install -g --prefix "${CONDA_DIR}" typescript typescript-language-server
npm cache clean --force
