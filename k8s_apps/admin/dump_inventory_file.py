import h5pyd
BUCKET="firefly-hsds"
inventory_domain = "/FIREfly/inventory.h5"
f = h5pyd.File(inventory_domain, "r", bucket=BUCKET)
table = f["inventory"]
for row in table:
    filename = row[0].decode('utf-8')
    start = row[1]
    stop = row[2]
    print(f"{filename}\t{start}\t{stop}")
print(f"{table.nrows} rows")
