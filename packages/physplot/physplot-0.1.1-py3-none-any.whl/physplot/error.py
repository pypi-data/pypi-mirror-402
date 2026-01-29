import numpy as np
from typing import Dict, Sequence, Union

NumberArray = Union[float, int, np.ndarray, Sequence[float]]

class Error:
    def __init__(self, err_data: NumberArray):
        self.err_data = np.array(err_data, dtype=float)
        self.mean_vals = None
        self.std_dev = None
        self.std_err = None

    def err(self, axis=-1, elementwise=False, print_std_err=False, print_mean=False, print_st_dev=False):
        data = self.err_data
        if elementwise:
            axis_to_use = -1
        else:
            axis_to_use = axis

        self.mean_vals = np.nanmean(data, axis=axis_to_use)
        self.std_dev = np.nanstd(data, axis=axis_to_use, ddof=1)
        n_points = data.shape[axis_to_use]
        self.std_err = self.std_dev / np.sqrt(n_points)

        if print_st_dev:
            print(f"Std Dev along axis {axis_to_use}:\n{self.std_dev}")
        if print_std_err:
            print(f"Std Err along axis {axis_to_use}:\n{self.std_err}")
        if print_mean:
            print(f"Mean along axis {axis_to_use}:\n{self.mean_vals}")
        return self.std_err