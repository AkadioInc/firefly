#!/usr/bin/env python3
import argparse
import h5py
import numpy as np
from firefly.util import aircraft_6dof, nearest_airport


parser = argparse.ArgumentParser(
    description=('Convert raw Ch10 1553 packet data to aircraft INS data. '
                 'Converted data are saved in the same HDF5 file.'),
    epilog='Copyright (c) 2019 Akadio Inc.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ffly', metavar='FILE', help='FIREfly input HDF5 file')
parser.add_argument('--print', '-p', action='store_true',
                    help='Print some derived data')
arg = parser.parse_args()

# Read in the appropriate 1553 data...
with h5py.File(arg.ffly, 'r') as f:
    fields = ('messages', 'msg_error', 'time')
    data = np.concatenate((
        f['/chapter11_data/1553/Ch_11/RT_6/SA_29/T/BC/data'][fields],
        f['/chapter11_data/1553/Ch_11/RT_6/SA_29/T/RT_27/SA_26/data'][fields]),
        axis=0)

# Proceed only if no message errors...
if np.any(data['msg_error']):
    raise ValueError('There are message errors in the data')

params = aircraft_6dof(data)
airport = nearest_airport(params['speed'], params['latitude'],
                          params['longitude'])

# Store engineering units data and related summary data...
with h5py.File(arg.ffly, 'a') as f:
    eu_grp = f.require_group('/derived')
    eu_grp.create_dataset('aircraft_ins', data=params, dtype=params.dtype,
                          chunks=True)

    # Inventory (summary) data...
    f.attrs['max_lat'] = params['latitude'].max()
    f.attrs['min_lat'] = params['latitude'].min()
    f.attrs['max_lon'] = params['longitude'].max()
    f.attrs['min_lon'] = params['longitude'].min()
    f.attrs['max_pitch'] = params['pitch'].max()
    f.attrs['min_pitch'] = params['pitch'].min()
    f.attrs['max_roll'] = params['roll'].max()
    f.attrs['min_roll'] = params['roll'].min()
    f.attrs['max_altitude'] = params['altitude'].max()
    f.attrs['min_altitude'] = params['altitude'].min()
    f.attrs['max_speed'] = params['speed'].max()
    f.attrs['min_speed'] = params['speed'].min()
    f.attrs['max_gforce'] = params['g-force'].max()
    f.attrs['min_gforce'] = params['g-force'].min()

    # Create/Update some global file metadata...
    dt = str(np.datetime64('now', 's')) + 'Z'
    f.attrs['date_modified'] = dt
    f.attrs['date_metadata_modified'] = dt
    f.attrs['takeoff_location'] = airport['takeoff']
    f.attrs['landing_location'] = airport['landing']

if arg.print:
    # Convert int64 values to numpy.datetime64 values...
    msgtime = params['time'].astype('datetime64[ns]')

    # Print some of the converted data...
    print('         Time              Speed     Longitude   Latitude  Altitude '
          'Heading     Roll     Pitch   g-force')
    for i in range(params.shape[0]):
        row = params[i]
        print(f"{str(msgtime[i])}   {row['speed']:.3f}   {row['longitude']:.5f}   "
              f"{row['latitude']:.5f}   {row['altitude']}   {row['heading']:5.1f}   "
              f"{row['roll']:7.3f}   {row['pitch']:7.3f}   {row['g-force']:6.3f}")
