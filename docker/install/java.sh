#!/bin/bash
# Java: JJava kernel (maintained fork of IJava). The JDK itself is copied
# from the `jdk` build stage into /opt/java.
set -euxo pipefail
JJAVA_VERSION=1.0-a8

java -version

cd /tmp
wget -q "https://github.com/dflib/jjava/releases/download/${JJAVA_VERSION}/jjava-${JJAVA_VERSION}-kernelspec.zip"
unzip -q "jjava-${JJAVA_VERSION}-kernelspec.zip" -d jjava
jupyter kernelspec install /tmp/jjava --sys-prefix --name=java
rm -rf /tmp/jjava "jjava-${JJAVA_VERSION}-kernelspec.zip"
