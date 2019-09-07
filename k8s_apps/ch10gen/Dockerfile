FROM python:3.7-alpine3.9
LABEL MAINTAINER="John Readey, Akadio Inc"
ENV AWS_ACCESS_KEY_ID=SupplyCorrectValue
ENV AWS_SECRET_ACCESS_KEY=SupplyCorrectValue
ENV AWS_S3_GATEWAY=http://s3.us-west-2.amazonaws.com
ENV AWS_REGION=us-west-2

RUN pip install awscli
ENV SRC_BUCKET=firefly-irig106

# copy convertor source and XLS files 
COPY BMtoCh10.tar /tmp/
COPY A10A-Echo-China_Lake.XLS /tmp/
COPY A10A-Echo-EdwardsAFB.XLS /tmp/
COPY A10A-R2915A-EglinAFB.XLS /tmp/
COPY entrypoint.sh  /

# copy python script
COPY gench10files.py /tmp/

# build BMtoCH10
RUN apk add --no-cache --virtual .build-deps build-base \
 && pip install awscli \
 && cd /tmp \
 && tar -xvf BMtoCh10.tar \
 && make \
 && cp BMtoCh10 /usr/local/bin 

 ENTRYPOINT ["/entrypoint.sh"]
