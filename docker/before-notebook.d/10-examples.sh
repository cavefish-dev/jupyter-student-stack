#!/bin/bash
# Refresh ~/examples from the pristine copy in the image on every start,
# so students always get the latest examples and can't break them for good.
# Run by the base image's start.sh (sourced: no `set -e`, no `exit`).

examples_src=/opt/examples
examples_dest="/home/${NB_USER:-jovyan}/examples"

if [ -d "${examples_src}" ]; then
    rm -rf "${examples_dest}" &&
        cp -r "${examples_src}" "${examples_dest}" ||
        echo "WARNING: could not refresh ${examples_dest}"
    if [ "$(id -u)" = 0 ]; then
        chown -R "${NB_UID:-1000}:${NB_GID:-100}" "${examples_dest}"
    fi
fi
