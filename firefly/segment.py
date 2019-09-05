##!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlopen
from hashlib import sha256
import numpy as np
import h5pyd as h5py
import pandas as pd
from ipyleaflet import (Map, Polyline, basemaps, basemap_to_tiles,
                        FullScreenControl, LayersControl)
import hvplot.pandas  # noqa
import Py106.Packet as Packet
try:
    from IPython.display import display
    display_map = True
except ImportError:
    display_map = False


class FlightSegment:
    """One flight segment, could be entire flight."""

    @staticmethod
    def chapter11_location(packet_type, **kwargs):
        """HDF5 group path name for specific IRIG 106 Chapter 10 packet type.

        Parameters
        ----------
        packet_type: int
            An IRIG 106 Chapter 10 packet type.
        kwargs: dict
            Packet type-specific named arguments.
        """
        top_group = '/chapter11_data'
        if packet_type == Packet.DataType.MIL1553_FMT_1:
            channel = kwargs.get('ch')
            from_rt = kwargs.get('from_rt')
            from_sa = kwargs.get('from_sa')
            to_rt = kwargs.get('to_rt')
            to_sa = kwargs.get('to_sa')

            # Sanity checks...
            if (not channel and any(
                    [a is not None for a in [from_rt, from_sa, to_rt, to_sa]])):
                raise ValueError('1553 channel not given')
            if from_sa and not from_rt:
                raise ValueError('"from_sa" given without "from_rt"')
            if to_sa and not to_rt:
                raise ValueError('"to_sa" given without "to_rt"')

            h5path = top_group + '/' + Packet.DataType.TypeName(packet_type)
            if channel:
                h5path += f'/Ch_{int(channel)}'
            else:
                return h5path
            if from_rt and to_rt:
                if not from_sa:
                    raise ValueError('"from_sa" not given')
                elif not to_sa and to_rt != 'BC':
                    raise ValueError('"to_sa" not given')
                h5path += f'/RT_{int(from_rt)}/SA_{int(from_sa)}/T'
                if to_rt == 'BC':
                    return h5path + '/BC'
                else:
                    return h5path + f'/RT_{int(to_rt)}/SA_{int(to_sa)}'
            elif from_rt and not to_rt:
                h5path += f'/RT_{int(from_rt)}'
                if from_sa:
                    return h5path + f'/SA_{int(from_sa)}'
                else:
                    return h5path
            elif to_rt and not from_rt:
                if not to_sa:
                    raise ValueError('"to_sa" not given')
                return h5path + f'/RT_{int(to_rt)}/SA_{int(to_sa)}/R/BC'
            else:
                # Return with just channel in the path...
                return h5path
        elif packet_type == Packet.DataType.VIDEO_FMT_0:
            h5path = top_group + '/' + Packet.DataType.TypeName(packet_type)
            channel = kwargs.get('ch')
            if channel:
                return h5path + f'/Ch_{int(channel)}'
            else:
                return h5path
        elif packet_type == Packet.DataType.TMATS:
            return top_group + '/' + Packet.DataType.TypeName(packet_type)
        else:
            raise ValueError(f'{packet_type}: Unsupported Ch10 packet type')

    def __init__(self, domain, mode, **kwargs):
        """Open FIREfly HDF5 file for access.

        Parameters
        ----------
        domain: str
            HDF Kita domain endopoint.
        mode: {'a', 'r'}
            Access mode. Only allowed: read and append.
        kwargs: dict
            Any other named argument is passed to the ``h5pyd.File`` class.
        """
        if mode not in ('a', 'r'):
            raise ValueError('mode can only be "a" or "r"')
        self._domain = h5py.File(domain, mode, **kwargs)
        self._other = kwargs
        data = pd.DataFrame(self._domain['/derived/aircraft_ins'][...])
        self._flight = data.astype({'time': 'datetime64[ns]'})
        self._flight.set_index('time', inplace=True)
        self._bbox = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._domain.close()

    def __repr__(self):
        if self._domain.id:
            return (
                f'<FIREfly {self.__class__.__name__} "{self._domain.filename}" '
                f'(mode "{self._domain.mode}")>')
        else:
            return '<Closed FIREfly HDF5 file>'

    def filter(self, cond):
        """Filter flight segment data into a new segment.

        Parameters
        ----------
        cond : str
            Condition (expression) for filtering flight segment data.

        Returns
        -------
        firefly.FlightSegment
            New flight segment with the data that matched filtering condition.
        """
        data = self._flight.query(cond, inplace=False)
        new_seg = self.__new__(type(self))
        new_seg._domain = h5py.File(self._domain.filename, self._domain.mode,
                                    **self._other)
        new_seg._other = self._other
        new_seg._flight = data
        new_seg._bbox = None
        return new_seg

    def close(self):
        """Close FIREfly file."""
        self._domain.close()

    @property
    def uri(self):
        """Flight segment's Kita URI."""
        return self._domain.id.http_conn.endpoint + self._domain.filename

    @property
    def start_time(self):
        """Start time of the flight segment.

        Returns
        -------
        pandas.Timestamp
            Start time of the flight segment.
        """
        return self._flight.index.min()

    @property
    def end_time(self):
        """End time of the flight segment.

        Returns
        -------
        pandas.Timestamp
            End time of the flight segment.
        """
        return self._flight.index.max()

    @property
    def bbox(self):
        """Flight segment's geospatial bounding box.

        Returns
        -------
        numpy.rec.array
            A scalar with four fields: ``max_lat``, ``min_lat``, ``max_lon``,
            ``min_lon``.
        """
        if self._bbox is None:
            max_lat = self._flight['latitude'].max()
            min_lat = self._flight['latitude'].min()
            max_lon = self._flight['longitude'].max()
            min_lon = self._flight['longitude'].min()
            self._bbox = np.rec.array((max_lat, min_lat, max_lon, min_lon),
                                      dtype=[('max_lat', max_lat.dtype),
                                             ('min_lat', min_lat.dtype),
                                             ('max_lon', max_lon.dtype),
                                             ('min_lon', min_lon.dtype)])
        return self._bbox

    @property
    def tmats(self):
        """A dictionary with TMATS attributes. Empty if no attributes."""
        tmats_h5path = '/derived/TMATS'
        tmats = dict()
        if tmats_h5path in self._domain:
            for n, v in self._domain[tmats_h5path].attrs.items():
                tmats[n] = v
        return tmats

    @property
    def takeoff(self):
        """Takeoff airport."""
        return self._domain.attrs['takeoff_location']

    @property
    def landing(self):
        """Landing airport."""
        return self._domain.attrs['landing_location']

    def info(self, pprint=False):
        """Overview of the flight's file content.

        Parameters
        ----------
        pprint: bool, optional
            Pretty-print the collected overview information instead.

        Returns
        -------
        dict
            Overview information as a dictionary.
        """
        info = dict()

        # Root group (global) attributes...
        info['global'] = list()
        for n, v in self._domain['/'].attrs.items():
            info['global'].append((n, v))

        # # Summary group attributes...
        # info['summary'] = list()
        # for n, v in self._domain['/summary'].attrs.items():
        #     info['summary'].append((n, v))

        # TMATS attributes...
        tmats = self.tmats
        info['TMATS'] = f'{len(tmats)} attributes'

        # Info on derived parameters...
        derived = self._domain['/derived']
        info['derived'] = list()

        def dset_info(name, obj):
            """A callable for collecting information about HDF5 datasets."""
            if not isinstance(obj, h5py.Dataset):
                return
            if obj.dtype.fields is None:
                d = {'shape': obj.shape,
                     'location': obj.name,
                     'datatype': str(obj.dtype)}
            else:
                d = {'shape': obj.shape,
                     'location': obj.name,
                     'fields': [(n, str(t[0])) for n, t in
                                obj.dtype.fields.items()]}
            info['derived'].append(d)

        derived.visititems(dset_info)

        if pprint:
            print(f'{self._domain.filename!r} overview:\n')
            if len(info['global']) > 0:
                print(f'Global attributes:\n------------------')
                for t in info['global']:
                    print(f'{t[0]} = {t[1]!r}')
                print('\n')

            print(f'TMATS: {info["TMATS"]}\n')

            # if len(info['summary']) > 0:
            #     print(f'Summary attributes:\n-------------------')
            #     for t in info['summary']:
            #         print(f'{t[0]} = {t[1]!r}')
            #     print('\n')

            if len(info['derived']) > 0:
                print(f'Available parameters:\n---------------------')
                for i in info['derived']:
                    print(f'{i["location"]} {i["shape"]!r}', end='')
                    if 'fields' in i:
                        print(' with fields:')
                        for _ in i['fields']:
                            print(f'    {_[0]} [{_[1]}]')
                    else:
                        print(f' {i["datatype"]}')

        else:
            return info

    def quickview(self, loc):
        """Quick view of parameter's data.

        Parameters
        ----------
        loc : str
            Parameter's location (HDF5 path name).
        """
        if not display_map:
            raise RuntimeError('Cannot display map')
        if loc != '/derived/aircraft_ins':
            raise ValueError(f'{loc}: No data')
        qv = self._flight.hvplot(
            y=['speed', 'altitude', 'roll', 'g-force', 'pitch'],
            width=500, height=300, subplots=True, shared_axes=False,
            padding=0.01).cols(2)
        display(qv)

    def flight_map(self, center=None, basemap=None, zoom=8):
        """Display interactive map of the flight path. (Jupyter notebook only.)

        Parameters
        ----------
        center: tuple, optional
            (latitude, longitude) center of the map. The default is the average
            of the flight's lat/lon bounding box.
        basemap: str, or list or tuple of str, optional
            Name of the base map available in ipyleaflet. Default:
            ``('Esri.WorldImagery', 'OpenTopoMap')``.
        zoom: int, optional
            Map zoom level. Default is 8.
        """
        if not display_map:
            raise RuntimeError('Cannot display map')
        if basemap is None:
            basemap = ('Esri.WorldImagery', 'OpenTopoMap')
        elif isinstance(basemap, str):
            basemap = (basemap,)
        elif not isinstance(basemap, (list, tuple)):
            raise TypeError('basemap is not a str, list, or tuple')
        base_layers = list()
        for layer in basemap:
            name_parts = layer.split('.')
            base_layer = basemaps
            for p in name_parts:
                base_layer = base_layer[p]
            if not isinstance(base_layer, dict):
                raise TypeError('base layer not a dict')
            base_layers.append(basemap_to_tiles(base_layer))
        data = self._flight
        flight_lat = data['latitude']
        flight_lon = data['longitude']
        if center is None:
            center = (flight_lat.mean(), flight_lon.mean())
        flight_path = Polyline(
            locations=[np.column_stack((flight_lat, flight_lon)).tolist()],
            color='blue', fill=False, name='Flight path')
        flight_map = Map(center=center, zoom=int(zoom))
        for _ in base_layers:
            flight_map.add_layer(_)
        flight_map.add_layer(flight_path)
        flight_map.add_control(FullScreenControl())
        flight_map.add_control(LayersControl())
        display(flight_map)

    def to_csv(self, outfile, loc, **kwargs):
        """Export specified data to CSV.
        """
        if isinstance(loc, str):
            # HDF5 path name...
            if loc != '/derived/aircraft_ins':
                raise ValueError(f'{loc}: No data')
            data = pd.DataFrame(self._domain[loc][...])
        elif isinstance(loc, int):
            # IRIG106 packet type...
            ch11_path = self.chapter11_location(loc, **kwargs)
            if ch11_path not in self._domain:
                raise ValueError(f'{ch11_path}: No data')
            grp = self._domain[ch11_path]
            if 'data' not in grp:
                raise ValueError(f'{ch11_path + "/data"}: No data')
            data = pd.DataFrame(grp['data'][...])
        else:
            raise TypeError(f'{loc}: Unsupported flight data specifier')

        data = data.astype({'time': 'datetime64[ns]'})
        data.set_index('time', inplace=True)
        data = data.loc[self.start_time:self.end_time]
        data.to_csv(outfile, mode='w', header=True, index=True)

    def download_ch10(self, outfile, verify=False):
        """Download flight Chapter 10 file.

        Parameters
        ----------
        outfile : str
            File path name for the downloaded Chapter 10 file. If it's an
            existing folder, the downloaded file will have the same name as the
            original Chapter 10 file in that folder.
        verify : {True, False}, optional
            Verify downloaded file against its SHA-256 checksum. Default is
            ``False``.
        """
        ch10_file = self._domain.attrs['ch10_file']
        of = Path(outfile)
        if of.is_dir():
            of = of.joinpath(ch10_file)

        endpoint = \
            f'https://firefly-chap10.s3-us-west-2.amazonaws.com/{ch10_file}'
        with urlopen(endpoint) as ch10, of.open('wb') as f:
            while True:
                chunk = ch10.read(10_000_000)
                if not chunk:
                    break
                else:
                    f.write(chunk)

        if verify:
            cksum = self._domain.attrs['ch10_file_checksum']
            if not cksum.startswith('SHA-256:'):
                raise ValueError(f'Ch10 file checksum is not SHA-256: {cksum}')

            new_cksum = sha256()
            with of.open('rb') as f:
                for chunk in iter(lambda: f.read(10_000_000), b''):
                    new_cksum.update(chunk)
            if cksum[8:] != new_cksum.hexdigest():
                raise IOError(f'{str(of)}: Different SHA-256 checksum ')
