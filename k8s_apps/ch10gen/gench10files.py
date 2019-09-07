import sys
import os
import random
import subprocess

from os import listdir, remove
from os.path import isfile

CH10_BUCKET="firefly-chap10"
AIRCRAFT_TYPES=["A10", "F-22", "F-35", "F-15", "F-15E", "F-16", "A10-C", "T-38" ]

def getRandStartTime():
    min_year = 2000
    max_year = 2019
    year = random.randint(min_year, max_year)
    month = random.randint(1,12)
    day = random.randint(1,28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{month:02d}-{day:02d}-{year}-{hour:02d}-{minute:02d}-{second:02d}"

input_files = [f for f in listdir(".") if isfile(f) and f.endswith("XLS")]
num_files = 1
if len(sys.argv) > 1:
    num_files = int(sys.argv[1])
elif "NUM_FILES" in os.environ:
    num_files = int(os.environ["NUM_FILES"])

print("AWS_SECRET_ACCESS_KEY:", os.environ["AWS_SECRET_ACCESS_KEY"])
print("AWS_ACCESS_KEY_ID:", os.environ["AWS_ACCESS_KEY_ID"])
            
print("num_files:", num_files)

for filename in input_files:
    print(filename)

for i in range(num_files):
    min_year = 2000
    max_year = 2019
    year = random.randint(min_year, max_year)
    month = random.randint(1,12)
    day = random.randint(1,28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    start_time = f"{month:02d}-{day:02d}-{year}-{hour:02d}-{minute:02d}-{second:02d}"

    type_index = random.randint(0, len(AIRCRAFT_TYPES)-1)
    aircraft_type = AIRCRAFT_TYPES[type_index]
    max_tail_code = num_files // 10
    if max_tail_code < 10:
        max_tail_code = 10
    elif max_tail_code > 1000:
        max_tail_code = 1000
    tail_code =  f"ED{type_index:02d}{random.randint(1, max_tail_code):04d}"
    input_file_index = random.randint(0, len(input_files) -1)
    input_filename = input_files[input_file_index]
    output_filename = f"{aircraft_type}-{tail_code}-{year}{month:02d}{day:02d}{hour:02d}{minute:02d}.ch10"
    print(input_filename, start_time, tail_code, aircraft_type)
    subprocess.run(["BMtoCh10", input_filename, output_filename, "-t", start_time])
    if not isfile(output_filename):
        sys.exit("BMtoCH10 failed")
    print(output_filename, "created")
    # copy to S3
    subprocess.run(["aws", "s3", "cp", output_filename, "s3://"+CH10_BUCKET, "--acl", "public-read"])
    remove(output_filename)
