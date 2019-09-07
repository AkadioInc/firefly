FROM firefly
LABEL MAINTAINER="John Readey, Akadio Inc"
ENV AWS_ACCESS_KEY_ID=SupplyCorrectValue
ENV AWS_SECRET_ACCESS_KEY=SupplyCorrectValue
ENV HSDS_ENDPOINT=http://100.65.5.116
ENV HS_USERNAME=jreadey@hdfgroup.org
ENV HS_PASSWORD=my_password

COPY convert_files.py /app
COPY entrypoint.sh  /

ENTRYPOINT ["/entrypoint.sh"]
