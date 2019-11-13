# FIREfly HDF5 Format Description

## Root (Global) HDF5 Attributes

|Attribute Name| Explanation |
|-|-|
| `aircraft_type` | Aircraft type. |
| `aircraft_id` | Aircraft serial/tail number.|
| `ch10_file` | Input Chapter 10 file name. |
| `ch10_file_checksum` | SHA-256 checksum of the input Chapter 10 file. |
| `takeoff_location` | Estimated (nearest) military takeoff location. |
| `landing_location` | Estimated (nearest) military landing location. |
| `time_coverage_start` | Chapter 10 data start UTC time in the ISO 8601 format. |
| `time_coverage_end` | Chapter 10 data end UTC time in the ISO 8601 format. |
| `date_created` | UTC datetime in the ISO 8601 format of the file's creation. |
| `date_modified` | UTC datetime in the ISO 8601 format of the last file's data content modification. |
| `date_metadata_modified` | UTC datetime in the ISO 8601 format of the last file's metadata content modification. |
| `max_speed` | Aircraft's maximum speed in knots. |
| `min_speed` | Aircraft's minimum speed in knots. |
| `max_altitude` | Aircraft's maximum altitude in feet. |
| `min_altitude` | Aircraft's minimum altitude in feet. |
| `max_lat` | Flight's northernmost latitude. |
| `min_lat` | Flight's southernmost latitude. |
| `max_lon` | Flight's easternmost longitude. |
| `min_lon` | Flight's westernmost longitude. |
| `max_pitch` | Aircraft's maximum pitch angle. Positive means up. |
| `min_pitch` | Aircraft's minimum pitch angle. Negative means down. |
| `max_roll` | Aircraft's maximum roll angle. Positive means clockwise. |
| `min_roll` | Aircraft's minimum roll angle. Negative means anticlockwise. |
| `max_gforce` | Maximum calculated flight G-force. |
| `min_gforce` | Minimum calculated flight G-force. |

## HDF5 Group: `/derived`

This group is for storing any data derived from the flight's Chapter 10 file content or are in some other way computationally related to the same flight. HDF5 objects in this group are:

|HDF5 Path Name| Purpose |
|:-|:-|
| `/derived/TMATS` | An HDF5 group with TMATS attributes from Chapter 10 file. One HDF5 attribute for one TMATS attribute. |
| `/derived/aircraft_ins` | A 1D compound HDF5 dataset with aircraft's flight location, six degrees of freedom (6DoF), and related parameters. |

`aircraft_ins` dataset's compound fields:

| Field Name | Explanation |
|:-|:-|
| `time` | POSIX time as nanoseconds. Specifically: numpy.datetime64[ns]. |
| `latitude` | Aircraft latitude. Positive is north. |
| `longitude` | Aircraft longitude. Positive is east. |
| `altitude` | Aircraft altitude in feet. |
| `speed` | Aircraft speed with regard to ground in knots. |
| `heading` | Aircraft true heading. |
| `roll` | Aircraft roll angle. Positive is clockwise. |
| `pitch` | Aircraft pitch angle. Positive is up. |
| `g-force` | Computed aircraft g-force. |

## HDF5 Group: `/chapter11_data`

Chapter 11 packet data extracted from a Chapter 10 file are stored under this group. These data are separated based on the packet type represented by the next sublevel of HDF5 groups. There can be a number of additional HDF5 groups depending on the packet type. Eventually, the last HDF5 group will have an HDF5 dataset named `data` holding the actual Chapter 11 data.

Supported Chapter 11 packet types and their `data` HDF5 dataset:

1. __MIL-STD-1553 Bus Data Packets, Format 1__

    `data`: one-dimensional compound HDF5 dataset with the following fields:

    | Field Name | Explanation |
    |:-|:-|
    | `time` | numpy.datetime64[ns] time of 1553 packet messages. |
    | `timestamp` | UTC timestamp of 1553 packet messages in the `YYYY/MM/DD HH:MM:SS.FFF` format. |
    | `msg_error` | Message error flag. |
    | `ttb` | Time tag bits. |
    | `word_error` | Word count error flag. |
    | `sync_error` | Sync type error flag. |
    | `word_count_error` | Transmitted data words count error flag. |
    | `rsp_tout` | Response timeout error flag. |
    | `format_error` | Format error flag. |
    | `bus_id` | Message bus ID. Either "A" or "B". |
    | `packet_version` | 1553 packet version. |
    | `messages` | 1553 packet words. |

1. __TMATS__

    `data`: scalar HDF5 dataset of opaque datatype holding the TMATS packet buffer.

1. __Video Packets, Format 0 (Moving Picture Experts Group-2/H.264)__

    `data`: one-dimensional HDF5 dataset of opaque datatype. Each element holds one video transport stream packet of 188 bytes.

    The following command generates a playable video file from the `data` HDF5 dataset in the `/chapter11_data/Video Format 0/Ch_3` HDF5 group:

    ```sh
    $ h5dump -d "/chapter11_data/Video Format 0/Ch_3/data" -b FILE -o video.mpg firefly.h5
    ```
