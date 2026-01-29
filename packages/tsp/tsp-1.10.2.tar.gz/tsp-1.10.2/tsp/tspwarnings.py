import numpy as np


class DuplicateTimesWarning(UserWarning):
    """For when duplicate times are found in a file."""
    def __init__(self, times):
        self.times = times
    
    def _msg(self, times) -> str:
        m = f"Duplicate timestamps found: {times[np.where(times.duplicated())[0]]}. That's bad."
        return m
    
    def __str__(self):
        return self._msg(self.times)

class NonIncreasingTimesWarning(UserWarning):
    """For when non-increasing times are found in a file."""
    def __init__(self, times):
        self.times = times
    
    def _msg(self, times) -> str:
        n_bad = np.sum(np.diff(times.values) <= np.timedelta64(0, 'ns'))
        m = f"{n_bad} non-increasing timestamps found. That's bad."
        return m
    
    def __str__(self):
        return self._msg(self.times)