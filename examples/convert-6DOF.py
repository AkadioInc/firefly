#!/usr/bin/env python3
from datetime import datetime
import numpy as np
import h5py


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
with h5py.File('A10-120_TerrainFollow_50_Seconds.h5', 'r') as f:
    msg_words = np.concatenate((
        f['/raw/1553/Ch_11/RT_6/SA_29/T/BC/data'][...],
        f['/raw/1553/Ch_11/RT_6/SA_29/T/RT_27/SA_26/data'][...]),
        axis=0)
    msg_error_flag = np.concatenate((
        f['/raw/1553/Ch_11/RT_6/SA_29/T/BC/msg_error'][...],
        f['/raw/1553/Ch_11/RT_6/SA_29/T/RT_27/SA_26/msg_error'][...]),
        axis=0)
    tstamp = np.concatenate((
        f['/raw/1553/Ch_11/RT_6/SA_29/T/BC/timestamp'][...],
        f['/raw/1553/Ch_11/RT_6/SA_29/T/RT_27/SA_26/timestamp'][...]),
        axis=0)

# Proceed only if no message errors...
if np.any(msg_error_flag):
    raise ValueError('There are message errors in the data')

# Concatenate all 1553 message words into one buffer then convert it into a
# NumPy structured array...
ins = np.frombuffer(b''.join([msg.tobytes() for msg in msg_words]),
                    dtype=ins_dt)

# Sort message words based on their time stamp...
sort_idx = np.argsort(tstamp)
tstamp = tstamp[sort_idx]
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

print('         Time              Speed     Longitude   Latitude  Altitude '
      'Heading     Roll     Pitch   g-force')
for i in range(ins.shape[0]):
    print(f'{tstamp[i].decode("ascii")}   {speed[i]:.3f}   {lon[i]:.5f}   '
          f'{lat[i]:.5f}   {alt[i]}   {true_heading[i]:5.1f}   '
          f'{roll[i]:7.3f}   {pitch[i]:7.3f}   {acc[i]:6.3f}')

# Store engineering units data...
with h5py.File('A10-120_TerrainFollow_50_Seconds.h5', 'a') as f:
    eu_grp = f.require_group('/converted')

    t = eu_grp.create_dataset('timestamp', data=tstamp, chunks=True)
    t.attrs['standard_name'] = np.string_('time')
    t.dims.create_scale(t, 'timestamp')

    dset = eu_grp.create_dataset('latitude', data=lat, chunks=True)
    dset.attrs['units'] = np.string_('degrees_north')
    dset.attrs['standard_name'] = np.string_('latitude')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('longitude', data=lon, chunks=True)
    dset.attrs['units'] = np.string_('degrees_east')
    dset.attrs['standard_name'] = np.string_('longitude')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('pitch', data=pitch, chunks=True)
    dset.attrs['units'] = np.string_('degrees')
    dset.attrs['standard_name'] = np.string_('platform_pitch_fore_up')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('roll', data=roll, chunks=True)
    dset.attrs['units'] = np.string_('degrees')
    dset.attrs['standard_name'] = np.string_('platform_roll_starboard_down')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('heading', data=true_heading, chunks=True)
    dset.attrs['units'] = np.string_('degrees')
    dset.attrs['standard_name'] = np.string_('platform_course')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('altitude', data=alt, chunks=True)
    dset.attrs['units'] = np.string_('ft')
    dset.attrs['standard_name'] = np.string_('height_above_mean_sea_level')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('speed', data=speed, chunks=True)
    dset.attrs['units'] = np.string_('kt')
    dset.attrs['standard_name'] = np.string_('platform_speed_wrt_ground')
    dset.dims[0].attach_scale(t)

    dset = eu_grp.create_dataset('g-force', data=acc, chunks=True)
    dset.dims[0].attach_scale(t)

    # Update some global file metadata...
    dt = datetime.utcnow().isoformat() + 'Z'
    f.attrs['date_modified'] = np.string_(dt)
