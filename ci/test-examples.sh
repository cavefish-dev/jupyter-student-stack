#!/bin/bash
# Execute every example notebook in an image; fail if any cell errors.
# Usage: ci/test-examples.sh <image>
set -euo pipefail
image="${1:?usage: $0 <image>}"

docker run --rm --entrypoint bash "${image}" -c '
    set -e
    jupyter kernelspec list
    cd /tmp && cp -r /opt/examples run && cd run
    status=0
    for nb in *.ipynb; do
        echo "=== ${nb}"
        if jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=180 \
               --output "/tmp/run/out-${nb}" "${nb}" >/tmp/log 2>&1; then
            echo "    ok"
        else
            cat /tmp/log
            status=1
        fi
    done
    exit ${status}
'
