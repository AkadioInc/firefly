FROM python:3.7-alpine3.9
LABEL MAINTAINER="John Readey, Akadio Inc."
ENV AWS_ACCESS_KEY_ID=SupplyCorrectValue
ENV AWS_SECRET_ACCESS_KEY=SupplyCorrectValue
ENV AWS_S3_GATEWAY=http://s3.us-west-2.amazonaws.com
ENV AWS_REGION=us-west-2
ENV HS_ENDPOINT=http://100.65.5.116
ENV HS_USERNAME=firefly_admin
ENV HS_PASSWORD=SupplyCorrectValue
RUN apk add --no-cache --virtual .build-deps build-base \
        coreutils  \
        git \
        && pip install boto3 \
        && pip install numpy \
        && pip install git+https://git@github.com/HDFGroup/h5pyd \
        && pip install awscli \
        && pip install git+https://git@github.com/HDFGroup/h5pyd
        
RUN mkdir /app
COPY ch10_watchdog.py /app
COPY entrypoint.sh  /
WORKDIR /app
ENTRYPOINT ["/entrypoint.sh"]
