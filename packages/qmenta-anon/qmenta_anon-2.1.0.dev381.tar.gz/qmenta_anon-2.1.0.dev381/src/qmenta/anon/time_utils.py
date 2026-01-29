from calendar import monthrange
from datetime import datetime, timedelta


class TimeUtilsError(Exception):
    """
    Base class for time utils errors
    """

    pass


class TooLargeDeltaError(TimeUtilsError):
    """
    Too large difference between two times.
    """

    def __init__(self, t1, t2, max_delta):
        message = (
            "Too large time difference between {} and {}. "
            "Maximum allowed delta: {}."
        ).format(t1, t2, max_delta)
        super().__init__(self, message)


def monthdelta(d1, d2):
    """
    Calculates the difference in months between two timepoints
    """
    delta = 0
    while True:
        mdays = monthrange(d1.year, d1.month)[1]
        d1 += timedelta(days=mdays)
        if d1 <= d2:
            delta += 1
        else:
            break
    return delta


def calculate_passed_days(timestamp1, timestamp2):
    """
    Calculates the number of days between two timestamps.
    """
    if timestamp2 is None:
        return 0

    diff = timestamp1 - timestamp2
    min_sec = divmod(diff.days * 86400 + diff.seconds, 60)
    return min_sec[0] / (24 * 60)


class TimeAnonymise:
    """
    Anonymise time while keeping the relative time differences between
    different image files in a single session. Each TimeAnonymise object
    should be used to anonymise exactly one session.

    Attributes
    ----------
    target_base : datetime
        The target date that is the base for the returned anonymised
        datetimes
    source_base : datetime
        The source date that will be used to compute the time difference with
        new input dates. This will be the input date of the first
        anonymise_datetime() function call
    max_delta : timedelta
        The maximum difference between two datetimes that are acceptable
        to be anonymised by a single TimeAnonymise instance. We use this
        to avoid mistakes where multiple sessions are being anonymised
        with a single TimeAnonymise instance.
    """

    def __init__(self):
        # Noon on January 1, 1900.
        self.target_base = datetime(1900, 1, 1, 12)
        # Will be set by the first input date
        self.source_base = None
        self.max_delta = timedelta(hours=24)

        # The minimum and maximum input times
        self._source_min = None
        self._source_max = None

    def anonymise_datetime(self, source):
        """
        Anonymise the input datetime by changing the date to be in the range
        (targetBase - 24h, targetBase + 24h) without changing the relative
        time difference between two any two times that were anonymised by this
        TimeAnonymise object.

        Parameters
        ----------
        source : datetime
            The datetime to anonymise

        Raises
        ------
        TooLargeDeltaError
            When the time difference between source and any of the previously
            anonymised datetime objects is more than max_delta.

        Returns
        -------
        datetime
            The anonymised datetime object
        """
        if self.source_base is None:
            # This is the first input to anonymise
            self.source_base = source
            self._source_min = source
            self._source_max = source
            return self.target_base

        if source < self._source_min:
            self._source_min = source
        elif source > self._source_max:
            self._source_max = source

        if (self._source_max - self._source_min) > self.max_delta:
            raise TooLargeDeltaError(source, self.source_base, self.max_delta)

        delta = source - self.source_base
        target = self.target_base + delta

        return target
