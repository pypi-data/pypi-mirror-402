import numba
import numpy as np


class StandardScaler:
    def fit_transform(s, x: np.ndarray):
        s.mean, s.std = x.mean(0), x.std(0)
        s.std[s.std == 0] = 1
        return s.transform(x)

    def transform(s, x) -> np.ndarray:
        return (x - s.mean) / s.std


@numba.njit(parallel=True)
def kernel_regression(x: np.ndarray, y, h, no_self=True, min_sum_w=1e-6):
    # x: (N, D), y: (N, ?), h: bandwidth
    N, _ = x.shape
    yp = np.zeros_like(y)
    C1 = 2.0 * (h**2)

    for i in numba.prange(N):
        sum_w = 0.0
        for j in range(N):
            if i == j and no_self:
                continue
            r2 = np.sum((x[i] - x[j]) ** 2)
            w = np.exp(-r2 / C1)
            sum_w += w
            yp[i] += w * y[j]
        if sum_w > min_sum_w:
            yp[i] /= sum_w
        else:
            yp[i, :] = np.nan
    return yp
