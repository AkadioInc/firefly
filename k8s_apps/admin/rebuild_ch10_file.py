import h5pyd
import sys

BUCKET="firefly-hsds"
inventory_domain = "/FIREfly/inventory.h5"

if len(sys.argv) <= 1 or sys.argv[1] in ("-h", "--help"):
    print("Usage: python rebuild_ch10_file [ch10_filename]")
    sys.exit(0)

ch10_filename = sys.argv[1]

f = h5pyd.File(inventory_domain, "a", bucket=BUCKET)
table = f["inventory"]
print(table.dtype)

condition = f"filename == b'{ch10_filename}'"
arr = table.read_where(condition, limit=1)
if len(arr) == 0:
    print("filename not found")
    sys.exit(1)

row = arr[0]
print(f"updating row: {row}")
update_val = {"start": 0, "done": 0}
table.update_where(condition, update_val, limit=1)
print("table updated")
