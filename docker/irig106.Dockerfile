FROM python:3.7-alpine3.9
LABEL MAINTAINER="Aleksandar Jelenak, Akadio Inc."
ARG IRIG106LIB_URL=https://github.com/bbaggerman/irig106lib/archive
ARG IRIG106LIB_BRANCH=master
RUN apk add --no-cache --virtual .build-deps \
        coreutils \
        gcc \
        libc-dev \
        make \
        curl \
        unzip \
# Download and build IRIG106LIB...
 && cd /tmp \
 && curl -L -o irig106lib.zip ${IRIG106LIB_URL}/${IRIG106LIB_BRANCH}.zip \
 && unzip irig106lib.zip \
 && cd irig106lib-${IRIG106LIB_BRANCH}/gcc \
 && make \
 # Copy shared and static IRIG106 library files to required locations...
 && cp -v *.so *a /usr/lib/ \
 && cp -v *.so ../python/Py106/ \
 # Uninstall build-related packages...
 && apk del .build-deps \
 # Copy Py106 package to the system Python default location...
 && cp -avr ../python/Py106/ $(python -c "import site; print(site.getsitepackages()[0])")/ \
 # Delete any temporary files...
 && cd /tmp \
 && rm -rf * \
# Update pip...
 && pip --no-cache-dir install -U pip \
 # Make a working directory...
 && mkdir /app

COPY ch10summary.py /app
VOLUME ["/data"]
WORKDIR /app
