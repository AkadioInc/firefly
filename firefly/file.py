##!/usr/bin/env python3
# import h5pyd as h5py
import h5py
import numpy as np
import Py106.Packet as Packet
from ipyleaflet import (Map, Polyline, basemaps, basemap_to_tiles,
                        FullScreenControl, LayersControl)
try:
    from IPython.display import display
    display_map = True
except ImportError:
    display_map = False


class File:
    """Represents one FIREfly HDF5 file."""

    @staticmethod
    def chapter11_h5path(packet_type, **kwargs):
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
                h5path += f'/RT_{int(from_rt)}/SA_{int(from_sa)}/T/'
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
            HDF Kita domain endopoint of the HDF5 file.
        mode: {'a', 'r'}
            Access mode. Only allowed: read and append.
        kwargs: dict
            Any other named argument is passed to the ``h5pyd.File`` class.
        """
        if mode not in ('a', 'r'):
            raise ValueError('mode can only be "a" or "r"')
        self._dom = h5py.File(domain, mode, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._dom.close()

    def __repr__(self):
        if self._dom.id:
            return (f'<FIREfly HDF5 file "{self._dom.filename}" '
                    f'(mode "{self._dom.mode}")>')
        else:
            return '<Closed FIREfly HDF5 file>'

    def close(self):
        """Close FIREfly file."""
        self._dom.close()

    @property
    def tmats(self):
        """A dictionary with TMATS attributes. Empty if no attributes."""
        tmats_h5path = '/derived/TMATS'
        tmats = dict()
        if tmats_h5path in self._dom:
            for n, v in self._dom[tmats_h5path].attrs.items():
                tmats[n] = v
        return tmats

    def info(self, pprint=False):
        """Overview of the file's content.

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
        for n, v in self._dom['/'].attrs.items():
            info['global'].append((n, v))

        # Summary group attributes...
        info['summary'] = list()
        for n, v in self._dom['/summary'].attrs.items():
            info['summary'].append((n, v))

        # TMATS attributes...
        tmats = self.tmats
        info['TMATS'] = f'{len(tmats)} attributes'

        # Info on derived parameters...
        derived = self._dom['/derived']
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
            print(f'{self._dom.filename!r} overview:\n')
            if len(info['global']) > 0:
                print(f'Global attributes:\n------------------')
                for t in info['global']:
                    print(f'{t[0]} = {t[1]!r}')
                print('\n')

            print(f'TMATS: {info["TMATS"]}\n')

            if len(info['summary']) > 0:
                print(f'Summary attributes:\n-------------------')
                for t in info['summary']:
                    print(f'{t[0]} = {t[1]!r}')
                print('\n')

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
        data = self._dom['/derived/aircraft_ins']
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
