FROM python:3.7-alpine3.9
LABEL MAINTAINER="Aleksandar Jelenak, Akadio Inc."
RUN apk add --no-cache --allow-untrusted \
            --repository http://dl-3.alpinelinux.org/alpine/edge/testing \
        coreutils \
        gcc \
        libc-dev \
        make \
        curl \
        unzip \
        binutils \
        git \
        hdf5 \
        hdf5-dev \
 && pip --no-cache-dir install -U pip \
 && pip --no-cache-dir -v install h5py \
 && pip install git+https://git@github.com/HDFGroup/h5pyd 
ENV PYTHONPATH=/irig106lib/python
RUN mkdir /app
VOLUME ["/app", "/data", "/irig106lib"]
WORKDIR /app
ENTRYPOINT ["/bin/ash"]
