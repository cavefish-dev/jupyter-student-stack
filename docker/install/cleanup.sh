#!/bin/bash
# Run as root at the end of each install step: drop caches left in the
# student's home and give it back to the notebook user.
set -euxo pipefail

home="/home/${NB_USER}"
rm -rf "${home}/.npm" "${home}/.wget-hsts" "${home}/.cache"
chown -R "${NB_UID}:${NB_GID}" "${home}"
fix-permissions "${CONDA_DIR}"
fix-permissions "${home}"
