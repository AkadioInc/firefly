FROM ch10toh5
LABEL MAINTAINER="John Readey, Akadio Inc"
ENV AWS_ACCESS_KEY_ID=SupplyCorrectValue
ENV AWS_SECRET_ACCESS_KEY=SupplyCorrectValue
ENV AWS_S3_GATEWAY=http://s3.us-west-2.amazonaws.com
ENV AWS_REGION=us-west-2
ENV HS_ENDPOINT=http://100.66.25.138
ENV HS_USERNAME=firefly_admin
ENV HS_PASSWORD=SupplyCorrectValue

RUN apk add --no-cache git
RUN pip --no-cache-dir install awscli
RUN pip --no-cache-dir install git+https://github.com/HDFGroup/h5pyd.git --upgrade
COPY convert_files.py /app
COPY entrypoint.sh  /

ENTRYPOINT ["/entrypoint.sh"]
