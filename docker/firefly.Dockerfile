FROM python:3.7-alpine3.9
LABEL MAINTAINER="Aleksandar Jelenak, Akadio Inc"

ARG IRIG106_REPO=https://github.com/ajelenak/irig106lib
ARG IRIG106_BRANCH=FIREfly

ENV AWS_ACCESS_KEY_ID=SupplyCorrectValue
ENV AWS_SECRET_ACCESS_KEY=SupplyCorrectValue

COPY firefly-master.zip /tmp/firefly.zip

RUN apk add --no-cache --virtual .build-deps \
        coreutils \
        gcc \
        g++ \
        libc-dev \
        make \
        curl \
        git \
        unzip \
 && apk add --no-cache --allow-untrusted \
            --repository http://dl-3.alpinelinux.org/alpine/edge/testing \
        hdf5 \
        hdf5-dev \
        zeromq-dev \
        libjpeg-turbo-dev \
# Download and build IRIG106LIB...
 && cd /tmp \
 && curl -L -o irig106lib.zip ${IRIG106_REPO}/archive/${IRIG106_BRANCH}.zip \
 && unzip irig106lib.zip \
 && cd irig106lib-${IRIG106_BRANCH}/gcc \
 && make \
 # Copy shared and static IRIG106 library files to required locations...
 && cp -v *.so *a /usr/lib/ \
 && cp -v *.so ../python/Py106/ \
 # Copy Py106 package to the system Python default location...
 && cp -avr ../python/Py106/ $(python -c "import site; print(site.getsitepackages()[0])")/ \
# Update pip...
 && pip --no-cache-dir install -U pip \
# Install Python packages...
 && pip --no-cache-dir -v install h5py awscli \
 && pip --no-cache-dir install git+https://github.com/HDFGroup/h5pyd.git \
 # Install the firefly repository...
 && cd /tmp \
 && unzip firefly.zip \
 && cd firefly-master \
 && python setup.py install  \
 && cd .. \
 && rm -rf * \
 # Uninstall build-related packages...
 && apk del .build-deps \
 # Delete any temporary files...
 && cd /tmp \
 && rm -rf * \
 # Make a working directory...
 && mkdir /app

WORKDIR /app
