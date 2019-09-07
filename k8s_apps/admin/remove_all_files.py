import sys
import subprocess
import h5pyd

HSDS_BUCKET="firefly-hsds"
H5_FOLDER =  "/FIREfly/h5/"
folder = h5pyd.Folder(H5_FOLDER, bucket=HSDS_BUCKET)  # get folder object
domain_names = []
for domain in folder:
    domain_names.append(domain)
if not domain_names:
    print("no domains found!")
    sys.exit()

print(f"found {len(domain_names)} domains")
for domain_name in domain_names:
    domain = H5_FOLDER + domain_name
    print(f"removing {domain}")
    rc = subprocess.run(["hsrm", "--bucket", HSDS_BUCKET, domain])
    if rc.returncode > 0:
        print(f"unable to delete  {domain}")
        sys.exit(-1)

print("done!")
