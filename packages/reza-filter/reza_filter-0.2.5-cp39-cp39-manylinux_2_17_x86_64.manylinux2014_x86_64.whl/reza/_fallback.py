from __future__ import annotations
import numpy as np

def _gain_lowpass(freqs, fc, c, offset, d):
    return np.where(freqs <= fc, 1.0, np.exp(-c * ((freqs - fc) + offset) ** d))

def _gain_highpass(freqs, fc, c, offset, d):
    return np.where(freqs >= fc, 1.0, np.exp(-c * ((fc - freqs) + offset) ** d))

def _gain_bandpass(freqs, fc_low, fc_high, c, offset, d):
    return _gain_highpass(freqs, fc_low, c, offset, d) * _gain_lowpass(freqs, fc_high, c, offset, d)

def _auto_d(mode, freqs, *, fc=None, fc_low=None, fc_high=None,
            c=0.9, offset=1.0,
            initial_d=10.0, d_increment=5.0, threshold=1e-4, max_iter=200, max_d=1e6):
    d = float(initial_d)
    last_sharp = 0.0
    for _ in range(int(max_iter)):
        if d > max_d:
            break

        if mode == "lowpass":
            g = _gain_lowpass(freqs, fc, c, offset, d)
            idx = int(np.searchsorted(freqs, fc))
            idx = max(1, min(idx, len(g) - 2))
            sharp = abs(g[idx] - g[idx + 1])
        elif mode == "highpass":
            g = _gain_highpass(freqs, fc, c, offset, d)
            idx = int(np.searchsorted(freqs, fc))
            idx = max(1, min(idx, len(g) - 2))
            sharp = abs(g[idx] - g[idx - 1])
        else:
            g = _gain_bandpass(freqs, fc_low, fc_high, c, offset, d)
            i1 = int(np.searchsorted(freqs, fc_low))
            i2 = int(np.searchsorted(freqs, fc_high))
            i1 = max(1, min(i1, len(g) - 2))
            i2 = max(1, min(i2, len(g) - 2))
            sharp = (abs(g[i1] - g[i1 - 1]) + abs(g[i2] - g[i2 + 1])) / 2.0

        if abs(sharp - last_sharp) > threshold:
            last_sharp = sharp
            d += d_increment
        else:
            break

    return float(d)

def lowpass(data, fs, fc, *, axis=-1, c=0.9, offset=1.0, d=None,
            initial_d=10.0, d_increment=5.0, threshold=1e-4, max_iter=200, max_d=1e6):
    x = np.asarray(data, dtype=float)
    x_m = np.moveaxis(x, axis, -1)
    n = x_m.shape[-1]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    if d is None:
        d = _auto_d("lowpass", freqs, fc=fc, c=c, offset=offset,
                    initial_d=initial_d, d_increment=d_increment, threshold=threshold, max_iter=max_iter, max_d=max_d)
    gain = _gain_lowpass(freqs, fc, c, offset, d)
    Y = np.fft.rfft(x_m, axis=-1) * gain
    y = np.fft.irfft(Y, n=n, axis=-1)
    return np.moveaxis(y, -1, axis)

def highpass(data, fs, fc, *, axis=-1, c=0.9, offset=1.0, d=None,
             initial_d=10.0, d_increment=5.0, threshold=1e-4, max_iter=200, max_d=1e6):
    x = np.asarray(data, dtype=float)
    x_m = np.moveaxis(x, axis, -1)
    n = x_m.shape[-1]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    if d is None:
        d = _auto_d("highpass", freqs, fc=fc, c=c, offset=offset,
                    initial_d=initial_d, d_increment=d_increment, threshold=threshold, max_iter=max_iter, max_d=max_d)
    gain = _gain_highpass(freqs, fc, c, offset, d)
    Y = np.fft.rfft(x_m, axis=-1) * gain
    y = np.fft.irfft(Y, n=n, axis=-1)
    return np.moveaxis(y, -1, axis)

def bandpass(data, fs, fc_low, fc_high, *, axis=-1, c=0.9, offset=1.0, d=None,
             initial_d=10.0, d_increment=5.0, threshold=1e-4, max_iter=200, max_d=1e6):
    x = np.asarray(data, dtype=float)
    x_m = np.moveaxis(x, axis, -1)
    n = x_m.shape[-1]
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)

    if d is None:
        d = _auto_d("bandpass", freqs, fc_low=fc_low, fc_high=fc_high, c=c, offset=offset,
                    initial_d=initial_d, d_increment=d_increment, threshold=threshold, max_iter=max_iter, max_d=max_d)
    gain = _gain_bandpass(freqs, fc_low, fc_high, c, offset, d)
    Y = np.fft.rfft(x_m, axis=-1) * gain
    y = np.fft.irfft(Y, n=n, axis=-1)
    return np.moveaxis(y, -1, axis)
