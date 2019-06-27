# Available Docker Images

## `irig106.Dockerfile`

The purpose of this image is to provide a foundation for all other Docker images that require the IRIG106 library and its Py106 Python package. Builds on the official `python:3.7-alpine3.9` Docker image.

## `firefly-dev.Dockerfile`

Intended for FIREfly project development. Uses the official `python:3.7-alpine3.9` Docker image. Included are HDF5 library and h5py Python package. The image declares three volumes:

* `/app` directory for general project development work
* `/data` Ch10 file directory
* `/irig106lib` the directory of `git clone https://github.com/ajelenak/irig106lib.git`

```bash
$ docker run -it \
             -v <DIR1>:/app \
             -v <DIR2>/data:/data \
             -v <DIR3>:/irig106lib \
         <firefly-dev Docker image>
```
