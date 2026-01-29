import numpy as np
from sympy import diff, lambdify, Symbol, Expr
from typing import Dict, Sequence, Union
from .error import Error

NumberArray = Union[float, int, np.ndarray, Sequence[float]]

class Propagation:
    def __init__(self, error_objs: Dict[Symbol, Error] = None, axis=-1, manual_err_data = None, manual_err = None):
        self._error_objs = error_objs
        self.axis = axis
        self.manual_err = manual_err
        self.manual_err_data = manual_err_data

        if error_objs is not None:
            self._prepare_errors()


    def _prepare_errors(self):
        self.err_data = {}
        self.std_err = {}
        for symbol, err_obj in self._error_objs.items():
            if not hasattr(err_obj, "err_data"):
                raise TypeError(f"{symbol} is not an Error instance.")
            if getattr(err_obj, "std_err", None) is None:
                err_obj.std_err = err_obj.err(axis=self.axis)
            data = np.array(err_obj.err_data, dtype=float)
            stde = np.array(err_obj.std_err, dtype=float)

            if stde.ndim < data.ndim:
                stde = np.expand_dims(stde, axis=self.axis)

            self.err_data[symbol] = data
            self.std_err[symbol] = stde

    def propagator(self, func: Expr, vars_in_func=None) -> np.ndarray:
        if self.manual_err_data is not None and self.manual_err is not None:
            if vars_in_func is None:
                raise ValueError("Provide 'vars_in_func' when using manual error mode.")
            sigma_sq_sum = 0

            for v in vars_in_func:
                if v not in self.manual_err_data or v not in self.manual_err:
                    raise ValueError(f"Missing data or error for variable {v}")

                partial = diff(func, v)
                arg_arrays = [np.array(self.manual_err_data[var], dtype=float) for var in vars_in_func]
                f_partial = lambdify(vars_in_func, partial, modules=["numpy"])
                partial_vals = f_partial(*arg_arrays)
                sigma_sq_sum += (partial_vals * self.manual_err[v]) ** 2
                if isinstance(sigma_sq_sum, (Expr, Symbol)):
                    sigma_sq_sum = float(sigma_sq_sum.evalf())

            return np.sqrt(sigma_sq_sum)

        if self._error_objs is None:
            raise ValueError("No Error objects provided for automatic mode.")

        vars_in_func = sorted(func.free_symbols, key=lambda s: s.name)
        missing = [v for v in vars_in_func if v not in self._error_objs]
        if missing:
            raise ValueError(f"Missing Error objects for variables: {missing}")

        sigma_sq_sum = 0
        for v in vars_in_func:
            partial = diff(func, v)
            f_partial = lambdify(vars_in_func, partial, "numpy")
            arg_arrays = [self.err_data[var] for var in vars_in_func]
            partial_vals = f_partial(*arg_arrays)
            sigma_sq_sum += (partial_vals * self.std_err[v]) ** 2

        return np.sqrt(sigma_sq_sum)