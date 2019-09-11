# ch10gen

Utilities to create synthetic ch10 files

## Generating Synthetic Data

### BlueMax Flight Dynamics Simulation

BlueMax software is used to generate realistic aircraft dynamic data from a high 
level input scenario file. Scendario files, the files ending in .SCN describe a flight 
path using high level commands for takeoff, fly to a point in space, perform combat manuvers, 
and finally land. BlueMax software is Distribution C. Distribution is authorized only to U.S. 
Government agencies and their contractors.

https://www.dsiac.org/resources/models_and_tools/bluemax6

BlueMax produces a number of output data files include a whitespace delimited data 
file with a ".XLS" extension. Despite the ".XLS" filename extension this is not a 
real Excel file, but can be opened and conventiently viewed with Excel.

### BlueMax to Ch 10

The application BMtoCh10 is used to read a BlueMax XLS data file and convert it 
into 1553 Nav data in an IRIG 106 data file. BMtoCh10 was developed under Windows 
but can be compiled and run under Linux. The Linux source files are in the file 
BMtoCh10.tar.gz. The ususal untar and then make should make an executable. Run it 
with no command line parameters to get a brief usage message.

    BMtoCh10  Jul 29 2019 20:12:06
    Convert a Bluemax XLS simulation file to a Ch 10 1553 nav message file
    Usage: BMtoCh10 <input file> <output file> [flags]
       <filename> Input/output file names
       -t         Data start time m-d-y-h-m-s

If not data start time is specified the current time is used. Below is an example
command for data starting July 30, 2019 at 2:30pm.

    BMtoCh10 A10A-Echo-China_Lake.XLS A10A-Echo-China_Lake.ch10 -t 6-30-2019-14-30-00

## Building and running with Docker

To build the docker image run:

    $ docker build -t firefly/ch10gen .

To run the container:

    $ docker run --name ch10gen -d -e "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" -e "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" -t firefly/ch10gen <file_count>

Where file_count is the number of desired files to be created.