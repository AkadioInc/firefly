FROM firefly
LABEL MAINTINER="John Readey, Akadio Inc"

COPY firefly /app/firefly
COPY setup.py /app/firefly
COPY scripts /app/scripts
COPY scripts /app/firefly/scripts
COPY setup.py /app

RUN apk add --no-cache --virtual .build-deps build-base

ENV AWS_ACCESS_KEY_ID=SupplyCorrectValue
ENV AWS_SECRET_ACCESS_KEY=SupplyCorrectValue
