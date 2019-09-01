import h5pyd
from .segment import FlightSegment


class FlightCollection:
    """FlightCollection of FIREfly flight domains based on filter criteria."""

    def __init__(self, loc, pattern=None, query=None, mode=None, aircraft=None,
                 tail=None, altitude=None, latitude=None, longitude=None,
                 time=None, **kwargs):
        """A set of FIREfly domains that satisfy filter criteria.

        Parameters
        ----------
        loc : str
            A Kita server URI where FIREfly domains could be found.
        pattern : str
            A regex for filtering FIREfly domain names.
        query : str
            A boolean expression for filtering FIREfly domains based on their
            HDF5 attributes.
        mode : {'r', 'r+', 'w', 'w-', 'x', 'a'}
            Access mode to ``loc``. Default is ``'r'``.
        aircraft : str or list/tuple of str
            Aircraft type. When list/tuple, select all FIREfly flights with any
            of them.
        tail : str or list/tuple of str
            Aircraft tail (serial) number. Only FIREfly data from those aircraft
            will be selected.
        altitude : float, or list/tuple of two floats
            Flight altitude (height above ground) in feet. A single float
            means to select data with altitudes greater or equal to that
            value. A tuple of two floats represents an open interval of
            altitudes. A list of two floats represents a closed interval of
            altitudes.
        latitude : float, or list/tuple of two floats
            Flight latitude in degrees (positive north). A single float
            means to select data with latitudes greater or equal to that
            value. A tuple of two floats represents an open interval of
            latitudes. A list of two floats represents a closed interval of
            latitudes.
        longitude : float, or list/tuple of two floats
            Flight longitude in degrees (positive east) in the range [-180,
            180]. A single float means to select data with longitudes greater or
            equal to that value. A tuple of two floats represents an open
            interval of longitudes. A list of two floats represents a closed
            interval of longitudes.
        time : ISO 8601 str, or list/tuple of two ISO 8601 str
            A time instance in the format ``YYYY-MM-DDTHH:MM:SS.SSSSZ``. The
            fractions of a second and UTC time zone designator (``Z``) are
            optional. A single ISO 8601 str means to select data with flight
            time greater or equal to that value.
        kwargs : dict
            Named arguments with Kita server access information.
        """
        self._pattern = pattern
        self._query = query
        self._mode = mode or 'r'
        self._kwargs = kwargs

        dom_query = ''
        data_query = ''
        if aircraft:
            if isinstance(aircraft, str):
                dom_expr = f'aircraft_type == {aircraft!r}'
            elif isinstance(aircraft, (list, tuple)):
                temp = [f'aircraft_type == {a!r}' for a in aircraft]
                dom_expr = ' OR '.join(temp)
                dom_expr = f'({dom_expr})'
            else:
                raise TypeError(f'aircraft argument: {type(aircraft)}')
            dom_query = ' AND '.join(filter(bool, [dom_query, dom_expr]))

        if tail:
            if isinstance(tail, str):
                dom_expr = f'aircraft_id == {tail!r}'
            elif isinstance(tail, (list, tuple)):
                temp = [f'aircraft_id == {a!r}' for a in tail]
                dom_expr = ' OR '.join(temp)
                dom_expr = f'({dom_expr})'
            else:
                raise TypeError(f'aircraft argument: {type(aircraft)}')
            dom_query = ' AND '.join(filter(bool, [dom_query, dom_expr]))

        if altitude:
            dom_expr = ''
            data_expr = ''
            if isinstance(altitude, list):
                min_val, max_val = float(altitude[0]), float(altitude[1])
                dom_expr = f'max_latitude >= {min_val}'
                data_expr = f'(altitude >= {min_val} and altitude <= {max_val})'
            elif isinstance(altitude, tuple):
                min_val, max_val = float(altitude[0]), float(altitude[1])
                dom_expr = f'max_altitude > {min_val}'
                data_expr = f'(altitude > {min_val} and altitude < {max_val})'
            else:
                dom_expr = f'max_altitude >= {float(altitude)}'
                data_expr = f'altitude >= {float(altitude)}'
            dom_query = ' AND '.join(filter(bool, [dom_query, dom_expr]))
            data_query = ' AND '.join(filter(bool, [data_query, data_expr]))

        if latitude:
            dom_expr = ''
            data_expr = ''
            if isinstance(latitude, list):
                min_val, max_val = float(latitude[0]), float(latitude[1])
                dom_expr = f'max_latitude >= {min_val}'
                data_expr = f'(latitude >= {min_val} and latitude <= {max_val})'
            elif isinstance(latitude, tuple):
                min_val, max_val = float(latitude[0]), float(latitude[1])
                dom_expr = f'max_latitude > {min_val}'
                data_expr = f'(latitude > {min_val} and latitude < {max_val})'
            else:
                dom_expr = f'max_latitude >= {float(latitude)}'
                data_expr = f'latitude >= {float(latitude)}'
            dom_query = ' AND '.join(filter(bool, [dom_query, dom_expr]))
            data_query = ' AND '.join(filter(bool, [data_query, data_expr]))

        if longitude:
            dom_expr = ''
            data_expr = ''
            if isinstance(longitude, list):
                min_val, max_val = float(longitude[0]), float(longitude[1])
                dom_expr = f'max_longitude >= {min_val}'
                data_expr = f'(longitude >= {min_val} and longitude <= {max_val})'
            elif isinstance(longitude, tuple):
                min_val, max_val = float(longitude[0]), float(longitude[1])
                dom_expr = f'max_longitude > {min_val}'
                data_expr = f'(longitude > {min_val} and longitude < {max_val})'
            else:
                dom_expr = f'max_longitude >= {float(longitude)}'
                data_expr = f'longitude >= {float(longitude)}'
            dom_query = ' AND '.join(filter(bool, [dom_query, dom_expr]))
            data_query = ' AND '.join(filter(bool, [data_query, data_expr]))

        if time:
            dom_expr = ''
            data_expr = ''
            if isinstance(time, list):
                min_val, max_val = time[0], time[1]
                dom_expr = f'time_coverage_end >= {min_val!r}'
                data_expr = f'(time >= {min_val!r} and time <= {max_val!r})'
            elif isinstance(time, tuple):
                min_val, max_val = time[0], time[1]
                dom_expr = f'time_coverage_end > {min_val!r}'
                data_expr = f'(time > {min_val!r} and time < {max_val!r})'
            else:
                dom_expr = f'time_coverage_end >= {time!r}'
                data_expr = f'time >= {time!r}'
            dom_query = ' AND '.join(filter(bool, [dom_query, dom_expr]))
            data_query = ' AND '.join(filter(bool, [data_query, data_expr]))

        self._flight_filter = dom_query
        self._data_filter = data_query
        self._loc = h5pyd.Folder(loc, mode=mode, pattern=pattern,
                                 query=self._flight_filter,
                                 **kwargs)
        loc = self._loc.domain
        self._domains = [loc + d for d in self._loc]

    def __repr__(self):
        if self._loc:
            return (f'<FIREfly {self.__class__.__name__} "{self._loc.domain}" '
                    f'({len(self._domains)} flights) at 0x{id(self):x}>')
        else:
            return f'<Closed FIREfly {self.__class__.__name__}>'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __len__(self):
        return len(self._domains)

    def close(self):
        """Close FIREfly FlightCollection."""
        self._loc.close()
        self._loc = None

    @property
    def flights(self):
        """Iterator over selected FIREfly flights."""
        return iter(self._domains)

    @property
    def flight_filter(self):
        return self._flight_filter

    @property
    def data_filter(self):
        return self._data_filter

    def filter(self, cond=None):
        """Filter selected FIREfly flight data.

        Parameters
        ----------
        cond : str, optional
            A filtering expression to apply on all selected flights in the
            collection.

        Returns
        -------
        iterator
            Iterator over firefly.FlightSegment objects produced by applying
            filtering condition to this collection's flights.
        """
        cond = cond or self._data_filter
        for s in self.flights:
            seg = FlightSegment(s, mode='r', **self._kwargs)
            yield seg.filter(cond)
