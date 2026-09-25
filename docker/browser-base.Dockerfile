ARG BASE=ghcr.io/ninggggy/sgr-webenv-release-runtime:1
FROM ${BASE}
RUN python3 -m pip install --no-cache-dir playwright==1.55.0 greenlet==3.5.5 pyee==13.0.1 typing_extensions==4.16.0
RUN curl --fail --location --retry 3 https://storage.googleapis.com/chrome-for-testing-public/140.0.7339.207/linux64/chrome-linux64.zip -o /tmp/chrome.zip && unzip -q /tmp/chrome.zip -d /opt && rm /tmp/chrome.zip && useradd -m -u 1000 browser
ENV HOME=/tmp/home
USER 1000:1000
