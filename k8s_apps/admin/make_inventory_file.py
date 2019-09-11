import sys
import h5pyd

HSDS_BUCKET="firefly-hsds"
inventory_domain = "/FIREfly/inventory.h5"

if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
    print("usage: python make_inventory_file.py <firefly_admin_password>")
    sys.exit()

firefly_admin_pwd=sys.argv[1]

f = h5pyd.File(inventory_domain, "x", username="firefly_admin", password=firefly_admin_pwd, bucket=HSDS_BUCKET)
dt=[("filename", "S64"), ("start", "i8"), ("done", "i8")]
table = f.create_table("inventory", dtype=dt)

# make public read, and get acl
acl = {"userName": "default"}
acl["create"] = False
acl["read"] = True
acl["update"] = False
acl["delete"] = False
acl["readACL"] = True
acl["updateACL"] = False
f.putACL(acl)
f.close()

print(f"created inventory: {inventory_domain}")
