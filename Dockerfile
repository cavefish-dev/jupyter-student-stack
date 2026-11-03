# Jupyter Student Stack: one image per language plus a full image.
#
#   docker build --target full -t jupyter-student-stack .        (default: full)
#   docker build --target java -t jupyter-student-stack:java .
#
# Targets: base/python, java, javascript, c, sql, asm, full.
# Every image includes Python and Bash; each language image adds one kernel.
#
# Size rule: fix permissions in the same RUN that installs the files. A
# separate chown/fix-permissions layer stores a second copy of every file.

ARG BASE_IMAGE=quay.io/jupyter/minimal-notebook:latest

# ---------------------------------------------------------------------------
# jdk: build stage only. jlink a JDK with just the modules students and the
# JJava kernel need (~1/3 the size of the full JDK; java, javac, jshell work)
# ---------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS jdk
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-21-jdk-headless binutils && \
    jlink \
        --add-modules java.se,jdk.jshell,jdk.compiler,jdk.jdi,jdk.jdwp.agent,jdk.zipfs,jdk.unsupported,jdk.localedata,jdk.crypto.ec,jdk.charsets,jdk.httpserver \
        --strip-debug --no-man-pages --no-header-files --compress=zip-6 \
        --output /opt/java

# ---------------------------------------------------------------------------
# base: Python + Bash kernels, extensions, language server support
# ---------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS base

# Installed as the notebook user into ${CONDA_DIR} (the docker-stacks way).
# Node.js comes from conda-forge: ~100 MB instead of ~285 MB from apt.
RUN mamba install -y -c conda-forge nodejs && \
    mamba clean -afy && \
    pip install --no-cache-dir \
        nbgrader \
        nbgitpuller \
        jupyter-resource-usage \
        variable_inspector \
        jupyterlab_rise \
        jupyterlab-language-pack-es-ES \
        jupyterlab-lsp \
        python-lsp-server \
        bash_kernel && \
    python -m bash_kernel.install --sys-prefix && \
    npm install -g --prefix "${CONDA_DIR}" bash-language-server && \
    npm cache clean --force && \
    rm -rf "/home/${NB_USER}/.npm" "/home/${NB_USER}/.cache" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# Example notebooks: each image copies its own into /opt/examples (last layer,
# so editing a notebook doesn't rebuild the kernels); refreshed into ~/examples on every start
COPY docker/before-notebook.d/10-examples.sh /usr/local/bin/before-notebook.d/10-examples.sh

COPY --chown=${NB_UID}:${NB_GID} jupyter_server_config.py /home/${NB_USER}/.jupyter/jupyter_server_config.py

# ---------------------------------------------------------------------------
# One image per language
# ---------------------------------------------------------------------------
FROM base AS python
COPY examples/README.md examples/00-linux-bash-basics.ipynb examples/01-python-basics.ipynb /opt/examples/

FROM base AS java
COPY --from=jdk /opt/java /opt/java
ENV JAVA_HOME=/opt/java \
    PATH="/opt/java/bin:${PATH}"
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
COPY --from=jdk /opt/java /opt/java
ENV JAVA_HOME=/opt/java \
    PATH="/opt/java/bin:${PATH}"
USER root
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/java.sh && bash /tmp/install/cleanup.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/javascript.sh && bash /tmp/install/cleanup.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/c.sh && bash /tmp/install/cleanup.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    bash /tmp/install/sql.sh && bash /tmp/install/cleanup.sh
RUN --mount=type=bind,source=docker/install,target=/tmp/install \
    --mount=type=bind,source=kernels/asm,target=/tmp/asm-kernel,rw \
    bash /tmp/install/asm.sh && bash /tmp/install/cleanup.sh
COPY examples/ /opt/examples/
USER ${NB_UID}
