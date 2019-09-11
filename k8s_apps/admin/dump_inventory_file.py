import h5pyd
from datetime import datetime
import tzlocal

BUCKET="firefly-hsds"
inventory_domain = "/FIREfly/inventory.h5"

def formatTime(timestamp):
    local_timezone = tzlocal.get_localzone() # get pytz timezone
    local_time = datetime.fromtimestamp(timestamp, local_timezone)
    return local_time



f = h5pyd.File(inventory_domain, "r", bucket=BUCKET)
table = f["inventory"]
for row in table:
    filename = row[0].decode('utf-8')
    if row[1]:
        start = formatTime(row[1])
    else:
        start = 0
    if row[2]:
        stop = formatTime(row[2])
    else:
        stop = 0
    print(f"{filename}\t{start}\t{stop}")
print(f"{table.nrows} rows")
