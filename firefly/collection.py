import h5pyd
from .segment import FlightSegment, filter_builder


class FFlyRepo:
    """A repository of FIREfly and Ch10 flight files."""

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
        """Filter FIREfly files based on a condition.

        Other parameters
        ----------------
        kwargs: dict
            See the FlightCollection class documentation for supported filtering
            parameters.
        """
        return FlightCollection(self._loc, mode=self._mode, bucket=self._bucket,
                                **{**kwargs, **self._kwargs})


class FlightCollection:
    """Collection of FIREfly flight domains based on filter criteria."""

    def __init__(self, loc, **kwargs):
        """A set of FIREfly domains that satisfy filter criteria.

        Parameters
        ----------
        loc : str
            A Kita server URI where FIREfly flight data are hosted.

        Other parameters
        ----------------
        mode : str
            Access mode. Default is "r".
        pattern : str
            A Python regex for filtering FIREfly flight file names.
        query : str
            A boolean expression for filtering FIREfly flights' data.
        kwargs : dict
            Any remaining named arguments are assumed to be flight data
            filtering parameters or Kita server access information.
        """
        self._mode = kwargs.pop('mode', 'r')
        pattern = kwargs.pop('pattern', None)
        query = kwargs.pop('query', None)
        if query is None:
            self._flight_filter, self._data_filter = filter_builder(kwargs)
        else:
            self._flight_filter = query
            self._data_filter = None

        self._loc = h5pyd.Folder(loc, mode=self._mode, pattern=pattern,
                                 query=self._flight_filter,
                                 **kwargs)
        loc = self._loc.domain
        self._domains = [loc + d for d in self._loc]
        self._kwargs = kwargs

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
        """Iterator over FIREfly flights in the collection.

        This method bypasses filtering of flight data.

        Yields
        ------
        FlightSegment
            A flight from the collection with all its data.
        """
        for flt in self._domains:
            yield FlightSegment(flt, mode='r', **self._kwargs)

    @property
    def flight_filter(self):
        """FIREfly file filtering statement."""
        return self._flight_filter

    @property
    def data_filter(self):
        """Data filtering statement to apply to each flight file."""
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
        for s in self._domains:
            flight = FlightSegment(s, mode='r', **self._kwargs)
            for seg in flight.filter(cond):
                yield seg
