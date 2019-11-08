import numpy as np
import csv
from pathlib import Path


def great_circle_distance(from_lat, from_lon, to_lat, to_lon):
    """Compute great circle distance using the Haversine formula.

    The Earth is assumed to be a perfect sphere with radius of 6371 kilometers.

    Parameters
    ----------
    from_lat : numpy array or scalar
        Decimal latitude values in degrees. Must be the same shape as
        ``from_lon``.
    from_lon : numpy array or scalar
        Decimal longitude values in degrees. Must be the same shape as
        ``from_lat``.
    to_lat : numpy array or scalar
        Decimal latitude values in degrees. Must be the same shape as
        ``to_lon``.
    to_lon : numpy array or scalar
        Decimal longitude values in degrees. Must be the same shape as
        ``to_lat``.

    Returns
    -------
    numpy array
        Great circle distance in kilometers between specified from/to lat/lon
        locations.
    """
    R = 6_371
    from_lat, from_lon, to_lat, to_lon = map(
        np.radians, [from_lat, from_lon, to_lat, to_lon])
    dlat = from_lat - to_lat
    dlon = from_lon - to_lon
    a = np.square(np.sin(0.5 * dlat)) + np.cos(from_lat) * np.cos(to_lat) * \
        np.square(np.sin(0.5 * dlon))
    dist = 2 * R * np.arcsin(np.sqrt(a))
    return dist


def nearest_airport(speed, lat, lon):
    """Find nearest takeoff and landing military airports based on flight data.

    All input arguments must be of the same shape. The nearest airport location
    is estimated using the great circle distance.

    Parameters
    ----------
    speed : numpy array
        Aircraft flight speed.
    lat: numpy array
        Aircraft flight latitude.
    lon: numpy array
        Aircraft flight longitude.

    Returns
    -------
    dict
        Takeoff and landing airport names in ``takeoff`` and ``landing`` dict
        keys.
    """
    # File with military installation locations...
    mirta_file = Path(__file__).resolve().parent / 'FY18_MIRTA_Points.csv'
    with mirta_file.open('r') as csvfile:
        rdr = csv.reader(csvfile, delimiter=',')
        mirta = np.genfromtxt(('|'.join(r) for r in rdr),
                              delimiter='|', names=True, dtype=None,
                              encoding=None)

    # Find first and last aircraft location with speed greater than 50...
    takeoff, landing = np.where(speed > 50)[0][[0, -1]]
    takeoff_loc = mirta[
        np.argmin(great_circle_distance(lat[takeoff], lon[takeoff],
                                        mirta['LATITUDE'], mirta['LONGITUDE']))]
    landing_loc = mirta[
        np.argmin(great_circle_distance(lat[landing], lon[landing],
                                        mirta['LATITUDE'], mirta['LONGITUDE']))]
    return {
        'takeoff': f"{takeoff_loc['SITE_NAME']}, {takeoff_loc['STATE_TERR']}",
        'landing': f"{landing_loc['SITE_NAME']}, {landing_loc['STATE_TERR']}"}


def aircraft_6dof(ch11_data):
    """Compute aircraft location, 6DoF, and related parameters.

    Parameters
    ----------
    ch11_data : numpy structured array
        Numpy structured array with input Chapter 11 data. The assumption is
        that any bad packet messages were removed prior to calling this
        function.

    Returns
    -------
    numpy structured array
        The array fields are the computed parameters.
    """
    # Define a NumPy structured array datatype for 6-DOF 1553 message words...
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

    # Sort input Ch11 array based on message time...
    idx = np.argsort(ch11_data['time'])
    sort_data = ch11_data[idx]

    # Concatenate all 1553 message words into one buffer then convert it into a
    # NumPy structured array...
    ins = np.frombuffer(b''.join([m.tobytes() for m in sort_data['messages']]),
                        dtype=ins_dt)

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

    # Output Numpy structured array for computed parameters...
    param_dt = np.dtype([('time', sort_data['time'].dtype),
                         ('latitude', lat.dtype),
                         ('longitude', lon.dtype),
                         ('altitude', alt.dtype),
                         ('speed', speed.dtype),
                         ('heading', true_heading.dtype),
                         ('roll', roll.dtype),
                         ('pitch', pitch.dtype),
                         ('g-force', acc.dtype)])
    param = np.empty(sort_data['time'].shape, dtype=param_dt)
    param['time'] = sort_data['time']
    param['latitude'] = lat
    param['longitude'] = lon
    param['altitude'] = alt
    param['speed'] = speed
    param['heading'] = true_heading
    param['roll'] = roll
    param['pitch'] = pitch
    param['g-force'] = acc

    return param
