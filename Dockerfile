# Jupyter Student Stack: one image per language plus a full image.
#
#   docker build --target full -t jupyter-student-stack .        (default: full)
#   docker build --target java -t jupyter-student-stack:java .
#
# Targets: base/python, java, javascript, c, sql, asm, full.
# Every image includes Python and Bash; each language image adds one kernel.

ARG BASE_IMAGE=quay.io/jupyter/minimal-notebook:latest

# ---------------------------------------------------------------------------
# base: Python + Bash kernels, extensions, language server support
# ---------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS base

USER root

# Node.js is needed by the language servers
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Update notebook
RUN pip install --no-cache-dir --upgrade notebook==7.3.3

# Install extensions and the Bash kernel
RUN pip install --no-cache-dir \
        nbgrader \
        nbgitpuller \
        jupyter-resource-usage \
        variable_inspector \
        jupyterlab_rise \
        jupyterlab-language-pack-es-ES \
        jupyterlab-lsp \
        python-lsp-server \
        bash_kernel && \
    python -m bash_kernel.install --sys-prefix

# Install the language servers globally, where jupyterlab-lsp finds them
RUN npm install -g --prefix "${CONDA_DIR}" bash-language-server && \
    npm cache clean --force

# Example notebooks: each image copies its own into /opt/examples (last layer,
# so editing a notebook doesn't rebuild the kernels); refreshed into ~/examples on every start
COPY docker/before-notebook.d/10-examples.sh /usr/local/bin/before-notebook.d/10-examples.sh

COPY --chown=${NB_UID}:${NB_GID} jupyter_server_config.py /home/${NB_USER}/.jupyter/jupyter_server_config.py
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/cleanup.sh

USER ${NB_UID}

# ---------------------------------------------------------------------------
# One image per language
# ---------------------------------------------------------------------------
FROM base AS python
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb /opt/examples/

FROM base AS java
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/java.sh && bash /tmp/install/cleanup.sh
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb examples/02-java-basics.ipynb /opt/examples/
USER ${NB_UID}

FROM base AS javascript
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/javascript.sh && bash /tmp/install/cleanup.sh
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb examples/03-javascript-basics.ipynb /opt/examples/
USER ${NB_UID}

FROM base AS c
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/c.sh && bash /tmp/install/cleanup.sh
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb examples/04-c-basics.ipynb /opt/examples/
USER ${NB_UID}

FROM base AS sql
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/sql.sh && bash /tmp/install/cleanup.sh
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb examples/05-sql-basics.ipynb /opt/examples/
USER ${NB_UID}

FROM base AS asm
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    --mount=type=bind,source=kernels/asm,target=/tmp/asm-kernel,rw \
    bash /tmp/install/asm.sh && bash /tmp/install/cleanup.sh
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb examples/06-assembly-basics.ipynb /opt/examples/
USER ${NB_UID}

# ---------------------------------------------------------------------------
# full: every kernel and every example (default target)
# ---------------------------------------------------------------------------
FROM base AS full
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/java.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/javascript.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/c.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/sql.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    --mount=type=bind,source=kernels/asm,target=/tmp/asm-kernel,rw \
    bash /tmp/install/asm.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/cleanup.sh
COPY examples/ /opt/examples/
USER ${NB_UID}
