#!/bin/bash
# Execute every example notebook in place inside an image, saving the cell outputs.
# The folder is mounted where students see it (~/examples) and run as the normal user,
# so outputs like `pwd` and `whoami` match what students get.
# Usage: ci/execute-examples.sh <image> [examples-dir]
set -euo pipefail
image="${1:?usage: $0 <image> [examples-dir]}"
dir="$(cd "${2:-examples}" && (pwd -W 2>/dev/null || pwd))" # pwd -W: Windows path under Git Bash

chmod -R a+rwX "${dir}" # the container user (uid 1000) must be able to rewrite the files

docker run --rm --entrypoint bash \
    -v "${dir}:/home/jovyan/examples" -w /home/jovyan/examples \
    "${image}" -c '
        set -e
        for nb in *.ipynb; do
            echo "=== ${nb}"
            jupyter nbconvert --to notebook --execute --inplace \
                --ExecutePreprocessor.timeout=180 \
                --ExecutePreprocessor.record_timing=False \
                "${nb}"
        done
    '
