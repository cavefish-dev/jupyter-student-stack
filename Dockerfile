FROM jupyter/minimal-notebook:ubuntu-22.04

USER root

# Install dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    gcc \
    make \
    nodejs \
    openjdk-21-jdk \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Update notebook
RUN pip install --upgrade notebook==7.3.3

# Unpack and install iJava kernel
ADD https://github.com/SpencerPark/IJava/releases/download/v1.3.0/ijava-1.3.0.zip ijava-kernel.zip
RUN unzip ijava-kernel.zip -d ijava-kernel && \
    rm ijava-kernel.zip && \
    cd ijava-kernel && \
    python3 install.py --sys-prefix

# Install Ganymede
ADD https://github.com/allen-ball/ganymede/releases/download/v2.1.2.20230910/ganymede-2.1.2.20230910.jar ganymede.jar
RUN java -jar ganymede.jar -i --copy-jar=true --sys-prefix && rm ganymede.jar

# Install IJavascript
RUN npm install -g ijavascript && ijsinstall

# Install gnu C kernel
RUN pip install jupyter-c-kernel && install_c_kernel --sys-prefix

# Install sql kernel
RUN conda install -c conda-forge xeus-sqlite

# Install the language servers
RUN npm install --save-dev \
    bash-language-server \
    dockerfile-language-server-nodejs \
    javascript-typescript-langserver \
#    jedi-language-server \
#    julia-language-server \
#    pyright \
#    python-language-server \
#    python-lsp-server \
#    r-languageserver \
    sql-language-server 
#    texlab \
#    typescript-language-server \
#    unified-language-server \
#    vscode-css-languageserver-bin \
#    vscode-html-languageserver-bin \
#    vscode-json-languageserver-bin \
#    yaml-language-server

# Install extensions
RUN pip install nbgrader && \
    pip install nbgitpuller && \
    pip install jupyter-resource-usage && \
    pip install variable_inspector && \
    pip install jupyterlab_rise && \
    pip install jupyterlab-language-pack-es-ES


# Set user back to priviledged user.
RUN chown -R "$NB_USER" "/home/$NB_USER/.local"  "/home/$NB_USER/.ipython"
USER $NB_USER
COPY jupyter_server_config.py /home/$NB_USER/.jupyter/jupyter_server_config.py
# RUN jupyter labextension disable @jupyterlab/extensionmanager-extension
