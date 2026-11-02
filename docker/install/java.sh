#!/bin/bash
# Java: OpenJDK 21 + JJava kernel (maintained fork of IJava)
set -euxo pipefail
JJAVA_VERSION=1.0-a8

apt-get update
apt-get install -y --no-install-recommends openjdk-21-jdk-headless
rm -rf /var/lib/apt/lists/*

cd /tmp
wget -q "https://github.com/dflib/jjava/releases/download/${JJAVA_VERSION}/jjava-${JJAVA_VERSION}-kernelspec.zip"
unzip -q "jjava-${JJAVA_VERSION}-kernelspec.zip" -d jjava
jupyter kernelspec install /tmp/jjava --sys-prefix --name=java
rm -rf /tmp/jjava "jjava-${JJAVA_VERSION}-kernelspec.zip"
