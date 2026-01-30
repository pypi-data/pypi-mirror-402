import numpy as np
from scipy.interpolate import interp1d

_lookuptable = np.linspace(0, np.pi + 1e-9, 10001)
_sinc_values = np.sinc(_lookuptable / np.pi)

_interpolator = interp1d(
    x=_sinc_values,
    y=_lookuptable,
    kind='linear',
    bounds_error=False,
    fill_value=(0, np.pi)
)


def inv_sinc(x):
    """Inverse Sinc function.

    Args:
        x (float or np.ndarray): Normalized Amplitude (0.0 ~ 1.0)

    Returns:
        float or np.ndarray: Phase value (0.0 ~ -pi)
    """
    return _interpolator(x)


_lookuptable_minus = np.linspace(-np.pi, 0, 10001)
_sinc_values_minus = np.sinc(_lookuptable_minus / np.pi)

_interpolator_minus = interp1d(
    x=_sinc_values_minus,
    y=_lookuptable_minus,
    kind='linear',
    bounds_error=False,
    fill_value=(-np.pi, 0)
)


def inv_sinc_minus(x):
    """Inverse Sinc function in minus domain.

    Args:
        x (float or np.ndarray): Normalized Amplitude (0.0 ~ 1.0)

    Returns:
        float or np.ndarray: Phase value (-pi ~ 0.0)
    """
    return _interpolator_minus(x)


def diffraction(l, n, res):
    data_array = np.zeros((res[0], res[0]), dtype=float)
    if l == 0 or n == 0:
        return data_array

    N_list = list(range(n))
    index_list = np.arange(0, l, int(l / n))
    dlist = np.linspace(0, res[0] - l, int(res[0] / l))
    d = 2 * np.pi * ((n - 1) / n)

    add_list = np.linspace(0, d, n)
    step_list = []
    for i in index_list:
        for j in range(int(l / n)):
            step_list.append(add_list[np.where(index_list == int(i))[0][0]])
    for i in dlist:
        for j in range(len(step_list)):
            data_array[j + int(i)] = step_list[j]
    return np.transpose(data_array)
