#!/bin/bash
# SQL: xeus-sqlite kernel + SQL language server
set -euxo pipefail

mamba install -y -c conda-forge xeus-sqlite
mamba clean -afy

npm install -g --prefix "${CONDA_DIR}" sql-language-server
npm cache clean --force
