import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from typing import Sequence, Union

NumberArray = Union[float, int, np.ndarray, Sequence[float]]

class Graph:
    def __init__(self, axis, x_axis, y_axis, marker='o', y_err = None, x_err = None, name = None):
        self.axis = axis
        self.marker = marker
        self.name = name
        self.y_err = y_err
        self.x_err = x_err
        self.x_axis_mean, self.x_err_mean = self._normalize_axis(x_axis, x_err)
        self.y_axis_mean, self.y_err_mean = self._normalize_axis(y_axis, y_err)
        self.parameters = None

    @staticmethod
    def plot_details(rows, cols, x_size, y_size, text=None, fontsize=None):
        fig, axs = plt.subplots(rows, cols, figsize=[x_size, y_size])
        if text is not None and fontsize is not None:
            fig.suptitle(text, fontsize=fontsize)
        if rows == 1 and cols == 1:
            axs = np.array([[axs]])
        elif rows == 1:
            axs = np.expand_dims(axs, axis=0)
        elif cols == 1:
            axs = np.expand_dims(axs, axis=1)
        return fig, axs

    def grapher(self, title=None, x_label=None, y_label=None, text=None, color=None, label=None,
                x_tick_start=None, x_tick_end=None, x_tick_step=None, y_tick_start=None,
                y_tick_end=None, y_tick_step=None, line_fit_bool=False,
                curve_fit_bool=False, fit_func=None, p0=None, fit_colors=None, fit_labels=None,
                minor_ticks=True):

        if self.y_err is not None or self.x_err is not None:
            self._handle_errors()
        dots = self.axis.scatter(self.x_axis_mean, self.y_axis_mean, marker=self.marker,
                                 color=color, label=label)

        if line_fit_bool:
            self._fit_line()
        if curve_fit_bool:
            self._fit_curve(fit_func, p0, fit_colors, fit_labels)
        self._set_ticks(x_tick_start, x_tick_end, x_tick_step,
                        y_tick_start, y_tick_end, y_tick_step, minor_ticks)
        self._finalize_plot(title, x_label, y_label, text)

        return dots

    def _handle_errors(self):
        def maybe_collapse(err):
            if err is None:
                return None
            err = np.array(err)
            if err.ndim > 1 and not (err.ndim == 2 and err.shape[0] == 2):
                return self._collapse_error(err)
            return err

        x_err_to_use = maybe_collapse(self.x_err_mean)
        y_err_to_use = maybe_collapse(self.y_err_mean)

        self.axis.errorbar(self.x_axis_mean, self.y_axis_mean, xerr=x_err_to_use, yerr=y_err_to_use, fmt='.', capsize=3,
            color='red', label="Error")

    def _fit_line(self):
        self.parameters = np.polyfit(self.x_axis_mean, self.y_axis_mean, 1)
        fit_line = np.polyval(self.parameters, self.x_axis_mean)
        self.axis.plot(self.x_axis_mean, fit_line, color='grey', linestyle='dashed', label='Linear Fit')

    def _fit_curve(self, fit_func, p0, fit_colors, fit_labels):
        if fit_func is None:
            raise ValueError("Provide fit_func for curve fitting.")
        fit_funcs = fit_func if isinstance(fit_func, (list, tuple)) else [fit_func]
        p0s = self._normalize_p0(fit_funcs, p0)
        fit_colors = self._normalize_list(fit_colors, len(fit_funcs))
        fit_labels = self._normalize_labels(fit_labels, len(fit_funcs))
        x_fit = np.linspace(min(self.x_axis_mean), max(self.x_axis_mean), 1000)
        self.parameters = []

        for i, func in enumerate(fit_funcs):
            try:
                popt, _ = curve_fit(func, self.x_axis_mean, self.y_axis_mean, p0=p0s[i])
                self.parameters.append(popt)
                fitted_y = func(x_fit, *popt)
                self.axis.plot(x_fit, fitted_y, color=fit_colors[i], linestyle='dashed', label=fit_labels[i])
            except Exception as e:
                print(f"Curve Fit {fit_labels[i]} failed: {e}")
                self.parameters.append(None)

    def _set_ticks(self, x_start, x_end, x_step, y_start, y_end, y_step, minor_ticks):
        if minor_ticks:
            self.axis.minorticks_on()
        if all(v is not None for v in [x_start, x_end, x_step]):
            self.axis.set_xticks(np.arange(x_start, x_end + x_step, x_step))
        if all(v is not None for v in [y_start, y_end, y_step]):
            self.axis.set_yticks(np.arange(y_start, y_end + y_step, y_step))

    def _finalize_plot(self, title, x_label, y_label, text):
        if title: self.axis.set_title(title, fontsize=12)
        if x_label: self.axis.set_xlabel(x_label)
        if y_label: self.axis.set_ylabel(y_label)
        if text:
            self.axis.text(0.5, 0.9, text, transform=self.axis.transAxes, fontsize=12, ha='center', color='blue')
        self.axis.legend()
        self.axis.grid()

    @staticmethod
    def _normalize_axis(axis_data, axis_err=None):
        axis_data = np.array(axis_data, dtype=float)
        if axis_data.ndim == 1:
            axis_mean = axis_data
            axis_err_mean = np.array(axis_err, dtype=float) if axis_err is not None else None
        else:
            axis_mean = np.nanmean(axis_data, axis=-1)
            if axis_err is not None:
                axis_err = np.array(axis_err, dtype=float)
                if axis_err.shape != axis_data.shape:
                    n_trials = axis_data.shape[-1]
                    axis_err_mean = axis_data.std(axis=-1, ddof=1) / np.sqrt(n_trials)
                else:
                    n_trials = axis_data.shape[-1]
                    axis_err_mean = np.nanmean(axis_err, axis=-1) / np.sqrt(n_trials)
            else:
                n_trials = axis_data.shape[-1]
                axis_err_mean = axis_data.std(axis=-1, ddof=1) / np.sqrt(n_trials)
        return axis_mean, axis_err_mean

    @staticmethod
    def _normalize_p0(funcs, p0):
        if p0 is None: return [None] * len(funcs)
        if len(funcs) == 1: return [list(p0) if isinstance(p0, (list, tuple, np.ndarray)) else [p0]]
        if all(isinstance(x, (list, tuple, np.ndarray)) for x in p0): return list(p0)
        return [list(p0)] * len(funcs)

    @staticmethod
    def _normalize_list(item, n):
        if item is None: return [None] * n
        if isinstance(item, (str, tuple)): return [item] * n
        return list(item)

    @staticmethod
    def _normalize_labels(labels, n):
        if labels is None: return [f"Fit {i+1}" for i in range(n)]
        if isinstance(labels, str): return [labels] * n
        return list(labels)

    @staticmethod
    def _collapse_error(err_array: np.ndarray) -> np.ndarray:
        err_array = np.array(err_array, dtype=float)

        if err_array.ndim == 0:
            return err_array
        elif err_array.ndim == 1:
            return err_array
        elif err_array.shape[0] == 2 and err_array.ndim == 2:
            return err_array
        else:
            collapsed = np.nanmean(err_array, axis=tuple(range(1, err_array.ndim)))
            return collapsed