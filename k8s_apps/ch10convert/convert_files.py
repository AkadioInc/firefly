import h5pyd
import logging
import time
import subprocess
import os

HSDS_BUCKET="firefly-hsds"
CH10_BUCKET="firefly-chap10"

inventory_domain = "/FIREfly/inventory.h5"
output_folder = "/FIREfly/h5/"

 
def convert_file(ch10_filename):
    print("convert_file:", ch10_filename)
    
    # extract aircraft type and tail number from filename
    base_name = ch10_filename[:-5]
    parts = base_name.split("-")
    if len(parts) < 3:
        print(f"unexpected filename (expected at least two hyphens): {ch10_filename}")
        return False
    aircraft_id = None
    aircraft_type = None
    if len(parts) >= 3:
        aircraft_id = parts[-2]
        aircraft_type = parts[0]
        if len(parts) > 3:
            # some type codes have a hyphen
            aircraft_type += "-"
            aircraft_type += parts[1]
        
    # convert to hdf5
    hdf5_filename = base_name + ".h5"
    print(f"converting to hdf5 file: {hdf5_filename} with aircraft_type: {aircraft_type} and aircraft_id: {aircraft_id}")
    convert_args = ["python", "/usr/local/bin/ch10-to-h5.py", "--outfile", hdf5_filename, "--aircraft-type", aircraft_type, "--aircraft-id", aircraft_id, ch10_filename ]
    # remove if more verbose logging is dessired
    convert_args.append("--loglevel")
    convert_args.append("warning")
    rc = subprocess.run(convert_args)
    if rc.returncode > 0:
        print(f"ch10-to-h5 convert error for {ch10_filename}")
        return False

    # update with derived data
    derive_args = ["python", "/usr/local/bin/derive-6dof.py", hdf5_filename]
    rc = subprocess.run(derive_args)
    if rc.returncode > 0:
        print(f"derive-6dof error for {hdf5_filename}")
        return False

    # upload to hsds
    domain_name = output_folder + hdf5_filename
    rc = subprocess.run(["hsload", "--bucket", HSDS_BUCKET, hdf5_filename, domain_name])
    if rc.returncode > 0:
        print(f"unable to load to hsds for {hdf5_filename}")

    # make the domain public read
    rc = subprocess.run(["hsacl", "--bucket", HSDS_BUCKET, domain_name, "+r", "default"])
    if rc.returncode > 0:
        print(f"unable to make public read for {domain_name}")
    
    # clean up the file
    os.remove(hdf5_filename)
    if rc.returncode == 0:
        return True
    else:
        return False

### main

loglevel = logging.ERROR
logging.basicConfig(format='%(asctime)s %(message)s', level=loglevel)

f = h5pyd.File(inventory_domain, "a", use_cache=False, bucket=HSDS_BUCKET)

table = f["inventory"]

condition = f"start == 0"  # query for files that haven't been proccessed

done = False
while not done:
    now = int(time.time())
    update_val = {"start": now}
    # query for row with 0 start value and update it to now
    indices = table.update_where(condition, update_val, limit=1)

    if len(indices) == 1:
        index = indices[0]
        print(f"getting row: {index}")
        row = table[index]
        ch10_filename = row[0].decode("utf-8")

        if not ch10_filename.endswith(".ch10"):
            print(f"unexpected filename (no ch10 extension): {ch10_filename}")
            continue

        # download ch10 file from s3
        s3_uri = f"s3://{CH10_BUCKET}/{ch10_filename}"
        rc = subprocess.run(["aws", "s3", "cp", s3_uri, ".", "--quiet"])
        if rc.returncode > 0:
            print(f"unable to copy {s3_uri}")
            continue

        if convert_file(ch10_filename):
            print(f"marking conversion of {ch10_filename} complete")
            row[2] = int(time.time())
            table[index] = row

        os.remove(ch10_filename) # remove the ch10 file from container
    
    else:
        # no available rows
        print("done!")

time.sleep(60)   # sleep for a bit to avoid endless restarts
print('exit')
