import numpy as np
from scipy.optimize import curve_fit, brentq
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern, WhiteKernel


# ---------------------------------------------------------------------------
# LSM helpers
# ---------------------------------------------------------------------------

def _linear(x, a, b):
    return a * x + b


def _quadratic(x, a, b, c):
    return a * x**2 + b * x + c


def _cubic(x, a, b, c, d):
    return a * x**3 + b * x**2 + c * x + d


def _exponential(x, a, b):
    return a * np.exp(b * x)


def _power(x, a, b):
    return a * np.power(np.abs(x), b)


def _logarithmic(x, a, b):
    return a * np.log(np.abs(x) + 1e-10) + b


_FUNCTIONS = {
    "linear": (_linear, [1.0, 0.0]),
    "quadratic": (_quadratic, [0.0, 1.0, 0.0]),
    "cubic": (_cubic, [0.0, 0.0, 1.0, 0.0]),
    "exponential": (_exponential, [1.0, 0.0]),
    "power": (_power, [1.0, 1.0]),
    "logarithmic": (_logarithmic, [1.0, 0.0]),
}


def get_lsm_function(func_type: str):
    """Return (function, initial_params) for the given function type."""
    return _FUNCTIONS.get(func_type, _FUNCTIONS["linear"])


def fit_lsm(hours, values, func_type: str):
    """Fit a curve using least squares. Returns (popt, pcov, func)."""
    func, p0 = get_lsm_function(func_type)
    x = np.array(hours, dtype=float)
    y = np.array(values, dtype=float)
    popt, pcov = curve_fit(func, x, y, p0=p0, maxfev=10000)
    return popt, pcov, func


def predict_lsm(func, popt, x_values):
    """Compute LSM function values at given x positions."""
    return func(np.asarray(x_values, dtype=float), *popt)


def find_critical_hours_lsm(
    func, popt, critical_value, is_decreasing, max_hours=1_000_000, x_start=0.0
):
    """
    Find the hour at which the LSM curve crosses critical_value.
    Returns None if no crossing is found in [x_start, max_hours].
    """
    # Avoid log/division by zero for functions that require x > 0
    lower = max(x_start, 0.01)

    def f(x):
        return func(x, *popt) - critical_value

    try:
        fa = f(lower)
        fb = f(float(max_hours))
        if fa * fb > 0:
            return None
        return brentq(f, lower, float(max_hours))
    except (ValueError, RuntimeError):
        return None


# ---------------------------------------------------------------------------
# GPR helpers
# ---------------------------------------------------------------------------

def _build_kernel(settings):
    length_scale = settings.gpr_length_scale
    noise_level = settings.gpr_noise_level
    kernel_type = settings.gpr_kernel_type

    if kernel_type == "rbf":
        return RBF(length_scale=length_scale)
    elif kernel_type == "matern":
        return Matern(length_scale=length_scale)
    elif kernel_type == "rbf+white":
        return RBF(length_scale=length_scale) + WhiteKernel(noise_level=noise_level)
    elif kernel_type == "matern+white":
        return Matern(length_scale=length_scale) + WhiteKernel(noise_level=noise_level)
    else:
        return RBF(length_scale=length_scale)


def fit_gpr(hours, values, settings):
    """Train a GPR model. Returns the fitted GaussianProcessRegressor."""
    x = np.array(hours, dtype=float).reshape(-1, 1)
    y = np.array(values, dtype=float)
    kernel = _build_kernel(settings)
    gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=3, normalize_y=True)
    gpr.fit(x, y)
    return gpr


def predict_gpr(gpr, x_values, confidence_level: float):
    """
    Predict with GPR and return (y_mean, y_lower, y_upper).
    confidence_level is the sigma multiplier (e.g. 2.0 for 95%).
    """
    x = np.asarray(x_values, dtype=float).reshape(-1, 1)
    y_mean, y_std = gpr.predict(x, return_std=True)
    y_lower = y_mean - confidence_level * y_std
    y_upper = y_mean + confidence_level * y_std
    return y_mean, y_lower, y_upper
