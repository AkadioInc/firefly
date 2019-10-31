import h5pyd
from .segment import FlightSegment


class FFlyRepo:
    """A repostiory of FIREfly and Ch10 flight files"""

    def __init__(self, loc, **kwargs):
        """
        Parameters
        ----------
        loc : str
            A Kita server URI where FIREfly flight data are hosted.

        Other parameters
        ----------------
        mode : {'r', 'r+', 'w', 'w-', 'x', 'a'}
            Access mode to ``loc``. Default is ``'r'``.
        kwargs : dict
            Any remaining named arguments with Kita server access information.
        """
        self._loc = loc
        self._mode = kwargs.pop('mode', 'r')
        self._bucket = kwargs.pop('bucket', None)
        self._kwargs = kwargs

    def __repr__(self):
        if self._loc:
            return (f'<{type(self).__name__} "{self._loc}" at 0x{id(self):x}>')
        else:
            raise ValueError(f'{type(self).__name__} not defined')

    def filter(self, **kwargs):
        """Filter FIREfly files based on a condition

        Other parameters
        ----------------
        kwargs: dict
            See the FlightCollection class documentation for supported filtering
            parameters.
        """
        return FlightCollection(self._loc, mode=self._mode, bucket=self._bucket,
                                **{**kwargs, **self._kwargs})


class FlightCollection:
    """FlightCollection of FIREfly flight domains based on filter criteria."""

    def __init__(self, loc, **kwargs):
        """A set of FIREfly domains that satisfy filter criteria.

        Parameters
        ----------
        loc : str
            A Kita server URI where FIREfly flight data are hosted.

        Other parameters
        ----------------
        pattern : str
            A regex for filtering FIREfly flight file names.
        query : str
            A boolean expression for filtering FIREfly flights' data.
        aircraft : str or list/tuple of str
            Aircraft type. When list/tuple, select all FIREfly flights with any
            of them.
        tail : str or list/tuple of str
            Aircraft tail (serial) number. Only FIREfly data from those aircraft
            will be selected.
        altitude : list or tuple
            Flight altitude (height above ground) in feet. The first list/tuple
            element represents minimal value; the second element the maximal
            value of the data to filter. If either of these values is ``None``
            that condition will not be included. The tuple represents an open
            interval. The list represents a closed interval.
        latitude : list or tuple
            Flight latitude in degrees (positive north). The first list/tuple
            element represents minimal value; the second element the maximal
            value of the data to filter. If either of these values is ``None``
            that condition will not be included. The tuple represents an open
            interval. The list represents a closed interval.
        longitude : list or tuple
            Flight longitude in degrees (positive east) in the range [-180,
            180].  The first list/tuple element represents minimal value; the
            second element the maximal value of the data to filter. If either of
            these values is ``None`` that condition will not be included. The
            tuple represents an open interval. The list represents a closed
            interval.
        time : list or tuple
            A time interval expressed as up to two ISO 8601 strings in the
            format ``YYYY-MM-DDTHH:MM:SS.SSSSZ``. The fractions of a second and
            UTC time zone designator (``Z``) are optional. The first list/tuple
            element represents minimal value; the second element the maximal
            value of the data to filter. If either of these values is ``None``
            that condition will not be included. The tuple represents an open
            interval. The list represents a closed interval.
        speed : list or tuple
            Aircraft ground speed in knots. The first list/tuple element
            represents minimal value; the second element the maximal value of
            the data to filter. If either of these values is ``None`` that
            condition will not be included. The tuple represents an open
            interval. The list represents a closed interval.
        kwargs : dict
            Any remaining named arguments with Kita server access information.
        """
        self._pattern = kwargs.pop('pattern', None)
        self._query = kwargs.pop('query', None)
        self._mode = kwargs.pop('mode', 'r')

        domain_query = ''
        data_query = ''
        for arg_name in ('aircraft', 'tail'):
            dom_expr = self._make_expr_str(arg_name, kwargs.pop(arg_name, None))
            domain_query = ' AND '.join(filter(bool, [domain_query, dom_expr]))

        for arg_name in ('altitude', 'latitude', 'longitude', 'speed'):
            dom_expr, data_expr = self._make_expr_float(arg_name,
                                                        kwargs.pop(arg_name,
                                                                   None))
            domain_query = ' AND '.join(filter(bool, [domain_query, dom_expr]))
            data_query = ' and '.join(filter(bool, [data_query, data_expr]))

        for arg_name in ('time',):
            dom_expr, data_expr = self._make_expr_time(arg_name,
                                                       kwargs.pop(arg_name,
                                                                  None))
            domain_query = ' AND '.join(filter(bool, [domain_query, dom_expr]))
            data_query = ' and '.join(filter(bool, [data_query, data_expr]))

        self._flight_filter = domain_query
        self._data_filter = data_query
        self._loc = h5pyd.Folder(loc, mode=self._mode, pattern=self._pattern,
                                 query=self._flight_filter,
                                 **kwargs)
        loc = self._loc.domain
        self._domains = [loc + d for d in self._loc]
        self._kwargs = kwargs

    def _make_expr_str(self, param_name, param_val):
        """Generate query expression from a string flight property."""
        if param_val is None:
            return

        attr_name = {'aircraft': 'aircraft_type',
                     'tail': 'aircraft_id'}
        attr = attr_name[param_name]

        if isinstance(param_val, str):
            flight_expr = f'{attr} == {param_val!r}'
        elif isinstance(param_val, (list, tuple)):
            temp = [f'{attr} == {a!r}' for a in param_val]
            flight_expr = '(' + ' OR '.join(temp) + ')'
        else:
            raise TypeError(
                f'{type(param_val)}: Invalid {param_name} value type')

        return flight_expr

    def _make_expr_float(self, param_name, param_val):
        """Generate query expression for a numeric flight parameter."""
        if param_val is None:
            return None, None

        # Summary attributes for each parameter...
        smmry_attr = {'altitude': ('min_altitude', 'max_altitude'),
                      'latitude': ('min_latitude', 'max_latitude'),
                      'longitude': ('min_longitude', 'max_longitude'),
                      'speed': ('min_speed', 'max_speed')}

        attr_min, attr_max = smmry_attr[param_name]

        if isinstance(param_val, list):
            oper = ('>=', '<=')
        elif isinstance(param_val, tuple):
            oper = ('>', '<')
        else:
            raise TypeError(
                f'{type(param_val)}: Invalid {param_name} value type')

        flight_expr = list()
        data_expr = list()
        for a, op, val in zip((attr_max, attr_min), oper, param_val):
            if val is None:
                continue
            else:
                val = float(val)
            data_expr.append(f'{param_name} {op} {val}')
            flight_expr.append(f'{a} {op} {val}')

        if len(flight_expr) > 1:
            flight_expr = '(' + ' AND '.join(filter(bool, flight_expr)) + ')'
            data_expr = '(' + ' and '.join(filter(bool, data_expr)) + ')'
        else:
            flight_expr = flight_expr[0]
            data_expr = data_expr[0]

        return (flight_expr, data_expr)

    def _make_expr_time(self, param_name, param_val):
        """Generate query expression for a time-valued flight parameter."""
        if param_val is None:
            return None, None

        # Summary attributes for each parameter...
        smmry_attr = {'time': ('time_coverage_start', 'time_coverage_end')}
        attr_min, attr_max = smmry_attr[param_name]

        if isinstance(param_val, list):
            oper = ('>=', '<=')
        elif isinstance(param_val, tuple):
            oper = ('>', '<')
        else:
            raise TypeError(
                f'{type(param_val)}: Invalid {param_name} value type')

        flight_expr = list()
        data_expr = list()
        for a, op, val in zip((attr_max, attr_min), oper, param_val):
            if val is None:
                continue
            data_expr.append(f'{param_name} {op} {val!r}')
            flight_expr.append(f'{a} {op} {val!r}')

        if len(flight_expr) > 1:
            flight_expr = '(' + ' AND '.join(filter(bool, flight_expr)) + ')'
            data_expr = '(' + ' and '.join(filter(bool, data_expr)) + ')'
        else:
            flight_expr = flight_expr[0]
            data_expr = data_expr[0]

        return (flight_expr, data_expr)

    def __repr__(self):
        if self._loc:
            return (f'<{self.__class__.__name__} with {len(self._domains)}'
                    f' flight(s) (repo: {self._loc.domain}) at 0x{id(self):x}>')
        else:
            return f'<Closed FIREfly {self.__class__.__name__}>'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __len__(self):
        return len(self._domains)

    def __getitem__(self, key):
        return self._domains[key]

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

    def apply(self, cond=None):
        """Apply filtering condition on FIREfly flights in the collection.

        Parameters
        ----------
        cond : str, optional
            A filtering expression to apply on all selected flights in the
            collection.

        Yields
        ------
        firefly.FlightSegment
            Flight segment produced by applying filtering to the selected
            flight.
        """
        cond = cond or self._data_filter
        for s in self.flights:
            flight = FlightSegment(s, mode='r', **self._kwargs)
            for seg in flight.filter(cond):
                yield seg
