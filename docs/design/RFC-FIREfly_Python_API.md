# RFC: FIREfly Python API

<!-- MDTOC maxdepth:6 firsth1:1 numbering:0 flatten:0 bullets:0 updateOnSave:1 -->

[RFC: FIREfly Python API](#RFC-FIREfly-Python-API)   
&emsp;[FIREfly Collection](#FIREfly-Collection)   
&emsp;[FIREfly File](#FIREfly-File)   
&emsp;&emsp;&emsp;&emsp;[`File(domain, mode='r', **kwargs)`](#Filedomain-moder-kwargs)   
&emsp;&emsp;&emsp;&emsp;[`File.info`](#Fileinfo)   
&emsp;&emsp;&emsp;&emsp;[`File.__str__`](#File__str__)   
&emsp;&emsp;&emsp;&emsp;[`File.tmats`](#Filetmats)   
&emsp;&emsp;&emsp;&emsp;[`File.map(center=None, zoom=12, basemap='OpenTopoMap')`](#FilemapcenterNone-zoom12-basemapOpenTopoMap)   
&emsp;&emsp;&emsp;&emsp;[`File.chapter11(packet, **kwargs)`](#Filechapter11packet-kwargs)   
&emsp;&emsp;&emsp;&emsp;[`File.get_param(h5path, labeled=False)`](#Fileget_paramh5path-labeledFalse)   
&emsp;&emsp;&emsp;&emsp;[`File.store_param(h5path, data, kind=None, units=None, label=None, **kwargs)`](#Filestore_paramh5path-data-kindNone-unitsNone-labelNone-kwargs)   
&emsp;&emsp;&emsp;&emsp;[`File.export_csv(object, fname)`](#Fileexport_csvobject-fname)   

<!-- /MDTOC -->

FIREfly Python API is a collection of Python modules, functions, and scripts in support of cloud-native flight test data analysis based on the FIREfly HDF5 files and the HDF Kita server. The goal is to provide simple and efficient interface for both programmatic and read-evaluate-print loop (REPL) workflows.

|Note: This document is expected to change in response to the development and needs of the project.|
| :-- |

Three main object classes are currently recognized: Collection, File, and Parameter. Each is further explained in the following text.

## FIREfly Collection

This class represents one collection (repository) of flight test data as FIREfly HDF5 files. The collection is identified with a URL representing a Kita server endpoint. The Collection API should support:

* filter/query/search operations on all FIREfly files in one collection;
* aggregate information about the entire collection, such as: number of files, data temporal coverage, etc.

The result of a filter/query operations is a list of FIREfly File objects that satisfy the operation's conditions.

## FIREfly File

This class represents one FIREfly HDF5 file with a Kita server endpoint. The proposed API is below:

##### `File(domain, mode='r', **kwargs)`

Open a FIREfly HDF5 file (a Kita domain) for access. This is just a passthrough to the h5pyd.File class.

##### `File.info`

General information about the file's data as JSON: temporal coverage, lat/lon bounding box, takeoff and landing airports, airplane type and ID, available Chapter 11 and derived data, etc.

##### `File.__str__`

The pretty-printed version of the `File.info` JSON output. Useful in Jupyter notebooks.

##### `File.tmats`

Return the h5pyd Group with TMATS attributes.

##### `File.map(center=None, zoom=12, basemap='OpenTopoMap')`

For use in Jupyter notebooks. Display an interactive map with the flight path. Optionally specify the map's center, zoom level, or the base map layer. If map's center is `None`, the average of the flight's lat/lon bounding box is used instead.

##### `File.chapter11(packet, **kwargs)`

Return the h5pyd Group where the packet data are. The `packet` argument is required and must be a Py106.Packet.DataType constant.

```python
from firefly import File
from Py106.Packet import DataType

ffly = File('/flights/test/example.h5')
grp1553 = ffly.chapter11(DataType.MIL1553_FMT_1, ch=11, from_rt=6, from_sa=22,
                         to_rt=13, to_sa=7)
video = ffly.chapter11(DataType.VIDEO_FMT_0, ch=2)
```

The `**kwargs` depend on the packet type.

##### `File.get_param(h5path, labeled=False)`

Get a derived parameter at `h5path` in the FIREfly file as an h5pyd.Dataset object. If `h5path` is a relative HDF5 path name (does not start with a "/") it will be interpreted starting from the `/derived` HDF5 group in the file.

When `labeled=True` and the parameter is a 1D array, the parameter will be returned as:

* A pandas.Series if the parameter's HDF5 datatype is atomic.
* A pandas.DataFrame if the parameter's HDF5 datatype is compound.

If the parameter has an HDF5 dimension scale (coordinate), it will be used as the label (index) when converting the parameter's data to the pandas object.

##### `File.store_param(h5path, data, kind=None, units=None, label=None, **kwargs)`

Store a 1D parameter in the FIREfly file. The parameter could be either derived from the Ch10 file content or computed in some other way. If `h5path` is a relative HDF5 path name (does not start with a "/") it will be interpreted starting from the `/derived` HDF5 group in the file.

Invoking this method will not only store the parameter data but also compute summaries of those data and update several attributes to indicate that the file's content has been modified. Storing parameter data using directly h5pyd will be possible but then the user will have to do all of this additional work as well.

```python
from firefly import File

ffly = File('/foo/bar/example.h5')
ffly.store_param(compute_airspeed(), kind='platform_speed_wrt_ground',
                 units='kt', label='time')
```

Optional arguments:

* `kind`: A unique identifier describing the type of data stored.

* `units`: A string representing data's physical units.

* `label`: One of:
  1. An HDF5 path name to a stored HDF5 dimension scale that provides the label (coordinate) values for the parameter's data. The dimension scale must have the same number of elements as the parameter array.
  1. `label=True` means that the parameter holds label (coordinate) data and will be stored as an HDF5 dimension scale.

* `**kwargs`: Other arguments

##### `File.export_csv(object, fname)`

Export data from the FIREfly file to a local CSV text file at `fname`. What data to export depends on the `object` type:

1. If `object` is an h5pyd.Group or a path name to a Chapter 11 HDF5 group in the file, each HDF5 dataset in that group will form one column of the exported CSV file.

1. If `object` is a tuple with elements being one of pandas.Series, h5pyd.Dataset or an HDF5 path name, each will form one column of the exported CSV file.

1. An exception if none of the above.
