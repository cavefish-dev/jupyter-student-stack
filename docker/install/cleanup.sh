#!/bin/bash
# Run as root in the SAME `RUN` as an install script: drop caches left in the
# student's home and give it back to the notebook user. (In a separate RUN,
# changing permissions would store a second copy of every file.)
set -euxo pipefail

home="/home/${NB_USER}"
rm -rf "${home}/.npm" "${home}/.wget-hsts" "${home}/.cache"
chown -R "${NB_UID}:${NB_GID}" "${home}"
fix-permissions "${CONDA_DIR}"
fix-permissions "${home}"
