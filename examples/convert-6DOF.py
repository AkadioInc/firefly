#!/usr/bin/env python3
import argparse
import csv
import numpy as np
import h5py
from pathlib import Path


parser = argparse.ArgumentParser(
    description=('Convert raw Ch10 1553 packet data to aircraft INS data. '
                 'Converted data are saved in the same HDF5 file.'),
    epilog='Copyright (c) 2019 Akadio Inc.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ffly', metavar='FILE', help='FIREfly input HDF5 file')
parser.add_argument('--print', '-p', help='Print some converted data')
arg = parser.parse_args()

# Define a NumPy structured array datatype for the 6-DOF 1553 message words...
ins_dt = np.dtype([('status', '<u2'),
                   ('time_tag', '<u2'),
                   ('vx_msw', '<i2'),
                   ('vx_lsw', '<u2'),
                   ('vy_msw', '<i2'),
                   ('vy_lsw', '<u2'),
                   ('vz_msw', '<i2'),
                   ('vz_lsw', '<u2'),
                   ('az', '<u2'),
                   ('roll', '<i2'),
                   ('pitch', '<i2'),
                   ('true_heading', '<u2'),
                   ('mag_heading', '<u2'),
                   ('accx', '<i2'),
                   ('accy', '<i2'),
                   ('accz', '<i2'),
                   ('cxx_msw', '<i2'),
                   ('cxx_lsw', '<u2'),
                   ('cxy_msw', '<i2'),
                   ('cxy_lsw', '<u2'),
                   ('cxz_msw', '<i2'),
                   ('cxz_lsw', '<u2'),
                   ('lon_msw', '<i2'),
                   ('lon_lsw', '<u2'),
                   ('alt', '<i2'),
                   ('steer_error', '<i2'),
                   ('tiltx', '<i2'),
                   ('tilty', '<i2'),
                   ('TBD', '<i2', (4,))])
assert ins_dt.itemsize == 64, '6-DOF numpy dtype must be 64 bytes long'

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

# Concatenate all 1553 message words into one buffer then convert it into a
# NumPy structured array...
ins = np.frombuffer(b''.join([msg.tobytes() for msg in data['messages']]),
                    dtype=ins_dt)

# Sort message words based on their time...
msgtime = data['time']
sort_idx = np.argsort(msgtime)
msgtime = msgtime[sort_idx]
ins = ins[sort_idx]

# Convert to engineering units...
lat = np.rad2deg(
    np.arcsin(
        np.bitwise_or(
            np.left_shift(ins['cxz_msw'], 16, dtype='i8'),
            ins['cxz_lsw']
        ) /
        0x40000000
    )
)

lon = (180. / 0x7fffffff) * np.bitwise_or(
    np.left_shift(ins['lon_msw'], 16, dtype='i8'),
    ins['lon_lsw'])

roll = (180. / 0x7fff) * ins['roll']

pitch = (180. / 0x7fff) * ins['pitch']

true_heading = (180. / 0x7fff) * ins['true_heading']

alt = ins['alt'] * 4.

acc = np.sqrt(
    np.square(np.right_shift(ins['accx'], 5), dtype='i4') +
    np.square(np.right_shift(ins['accy'], 5), dtype='i4') +
    np.square(np.right_shift(ins['accz'], 5), dtype='i4')) / 32

speed = (900. / 6080.) * np.sqrt(np.square(ins['vx_msw'], dtype='f4') +
                                 np.square(ins['vy_msw'], dtype='f4'))

# Figure out the takeoff and landing locations...
mirta_file = (Path(__file__).resolve().parent / '..' / 'firefly' /
              'FY18_MIRTA_Points.csv')
with mirta_file.open('r') as csvfile:
    rdr = csv.reader(csvfile, delimiter=',')
    mirta = np.genfromtxt(('|'.join(r) for r in rdr), delimiter='|', names=True,
                          dtype=None, encoding=None)
takeoff, land = np.where(speed > 50)[0][[0, -1]]
takeoff_loc = mirta[np.argmin(
    np.sqrt(np.square(lat[takeoff] - mirta['LATITUDE']) +
            np.square(lon[takeoff] - mirta['LONGITUDE'])))]
landing_loc = mirta[np.argmin(
    np.sqrt(np.square(lat[land] - mirta['LATITUDE']) +
            np.square(lon[land] - mirta['LONGITUDE'])))]

# Output Numpy structured array for computed parameters...
param_dt = np.dtype([('time', msgtime.dtype),
                     ('latitude', lat.dtype),
                     ('longitude', lon.dtype),
                     ('altitude', alt.dtype),
                     ('speed', speed.dtype),
                     ('heading', true_heading.dtype),
                     ('roll', roll.dtype),
                     ('pitch', pitch.dtype),
                     ('g-force', acc.dtype)])
param = np.empty(msgtime.shape, dtype=param_dt)
param['time'] = msgtime
param['latitude'] = lat
param['longitude'] = lon
param['altitude'] = alt
param['speed'] = speed
param['heading'] = true_heading
param['roll'] = roll
param['pitch'] = pitch
param['g-force'] = acc

# Store engineering units data and related summary data...
with h5py.File(arg.ffly, 'a') as f:
    eu_grp = f.require_group('/derived')
    eu_grp.create_dataset('aircraft_ins', data=param, dtype=param_dt,
                          chunks=True)

    # Inventory (summary) data...
    inv_grp = f.require_group('/summary')
    inv_grp.attrs['max_lat'] = lat.max()
    inv_grp.attrs['min_lat'] = lat.min()
    inv_grp.attrs['max_lon'] = lon.max()
    inv_grp.attrs['min_lon'] = lon.min()
    inv_grp.attrs['max_pitch'] = pitch.max()
    inv_grp.attrs['min_pitch'] = pitch.min()
    inv_grp.attrs['max_roll'] = roll.max()
    inv_grp.attrs['min_roll'] = roll.min()
    inv_grp.attrs['max_altitude'] = alt.max()
    inv_grp.attrs['min_altitude'] = alt.min()
    inv_grp.attrs['max_speed'] = speed.max()
    inv_grp.attrs['min_speed'] = speed.min()
    inv_grp.attrs['max_gforce'] = acc.max()
    inv_grp.attrs['min_gforce'] = acc.min()

    # Create/Update some global file metadata...
    dt = str(np.datetime64('now', 's')) + 'Z'
    f.attrs['date_modified'] = dt
    f.attrs['date_metadata_modified'] = dt
    f.attrs['takeoff_location'] = \
        f"{takeoff_loc['SITE_NAME']}, {takeoff_loc['STATE_TERR']}"
    f.attrs['landing_location'] = \
        f"{landing_loc['SITE_NAME']}, {landing_loc['STATE_TERR']}"

if arg.print:
    # Convert int64 values to numpy.datetime64 values...
    msgtime = msgtime.astype('datetime64[ns]')

    # Print some of the converted data...
    print('         Time              Speed     Longitude   Latitude  Altitude '
          'Heading     Roll     Pitch   g-force')
    for i in range(ins.shape[0]):
        print(f'{str(msgtime[i])}   {speed[i]:.3f}   {lon[i]:.5f}   '
              f'{lat[i]:.5f}   {alt[i]}   {true_heading[i]:5.1f}   '
              f'{roll[i]:7.3f}   {pitch[i]:7.3f}   {acc[i]:6.3f}')
