import time
import boto3
import h5pyd

CHAP10_BUCKET="firefly-chap10"
HSDS_BUCKET="firefly-hsds"
inventory_domain = "/FIREfly/inventory.h5"

s3_paginator = boto3.client('s3').get_paginator('list_objects_v2')

def keys(bucket_name, prefix='/', delimiter='/', start_after=''):
    prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
    start_after = (start_after or prefix) if prefix.endswith(delimiter) else start_after
    for page in s3_paginator.paginate(Bucket=bucket_name, Prefix=prefix, StartAfter=start_after):
        for content in page.get('Contents', ()):
            yield content['Key']

def watch_bucket():
    print("watch_bucket")
    f = h5pyd.File(inventory_domain, "a", bucket=HSDS_BUCKET)
    table = f["inventory"]
    for key in keys(CHAP10_BUCKET):
        condition = f"filename == b'{key}'"
        matches = table.read_where(condition, limit=1)
        if len(matches) == 0:
            print(f"not found, adding filename: {key}")
            row = (key, 0, 0)
            table.append([row,])
        else:
            pass  # filename found

#
# main
#

print("ch10_watchdog starting")
SLEEP_TIME=60 # one minute interval betwen checking the bucket

while True:
    watch_bucket()
    print(f"sleeping for {SLEEP_TIME} seconds")
    time.sleep(SLEEP_TIME)  # sleep for a bit
