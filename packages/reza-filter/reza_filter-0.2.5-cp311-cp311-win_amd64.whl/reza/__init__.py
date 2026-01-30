from __future__ import annotations

"""
Reza Filter (minimal, SciPy-like user-facing API)
------------------------------------------------
Goal: users should only need:

    import reza

    # SciPy-like (preferred)
    y = reza.filter(x, fs=200, Wn=5, btype="low")         # low-pass 5 Hz
    y = reza.filter(x, fs=200, Wn=10, btype="high")       # high-pass 10 Hz
    y = reza.filter(x, fs=200, Wn=(5, 10), btype="band")  # band-pass 5-10 Hz

    # Convenience wrappers
    y = reza.low(x,  fs=200, fc=5)
    y = reza.high(x, fs=200, fc=10)
    y = reza.band(x, fs=200, f1=5, f2=10)

Notes
-----
- Reza Filter is applied in the FFT domain as a zero-phase magnitude shaping curve.
- All shaping parameters are internal. The decay exponent d is auto-selected and cached.
- For frequency response, use reza.freqz(...). Unlike IIR filters, Reza's response
  depends on the effective FFT length; we choose an internal default automatically
  so users do not need to pass n.
"""

import math
from functools import lru_cache
import numpy as np

# Package version (must match installed distribution metadata)
try:
    from importlib.metadata import version as _pkg_version  # py3.8+
    __version__ = _pkg_version("reza-filter")
except Exception:
    __version__ = "0.0.0"

from . import _fallback

try:
    from . import _reza_cpp as _cpp  # compiled extension
    _HAS_CPP = True
except Exception:
    _cpp = None
    _HAS_CPP = False

__all__ = [
    # Primary (SciPy-like)
    "filter",
    "freqz",

    # Convenience wrappers
    "low",
    "high",
    "band",

    # Backward-compatible aliases
    "lowpass",
    "highpass",
    "bandpass",
    "lp",
    "hp",
    "bp",

    # Utilities
    "has_cpp",
    "__version__",
]

# ---------------------------------------------------------------------
# Internal defaults (NOT part of the public API)
# ---------------------------------------------------------------------
_C_DEFAULT = 0.9
_OFFSET_DEFAULT = 1.0

# Dynamic-decay search parameters (kept internal)
_D_INIT = 10.0
_D_INC = 5.0
_D_THRESHOLD = 1e-4
_D_MAX_ITER = 200
_D_MAX = 1e6

# Freq-response internal defaults (kept internal)
_FREQZ_MIN_N = 4096
_FREQZ_MAX_N = 262144
_FREQZ_MIN_DF_HZ = 0.02      # do not chase absurdly fine grids by default
_FREQZ_FMIN_FRAC = 1.0 / 100 # aim for ~100 points up to the smallest cutoff


def has_cpp() -> bool:
    return _HAS_CPP


def _move_axis_to_last(x: np.ndarray, axis: int) -> np.ndarray:
    return np.moveaxis(x, axis, -1) if axis != -1 else x


def _move_axis_back(x: np.ndarray, axis: int) -> np.ndarray:
    return np.moveaxis(x, -1, axis) if axis != -1 else x


def _apply_gain_rfft(X: np.ndarray, gain: np.ndarray) -> np.ndarray:
    if _HAS_CPP:
        return _cpp.apply_gain_rfft(X, gain)
    return _fallback.apply_gain_rfft(X, gain)


@lru_cache(maxsize=256)
def _auto_d_lowpass(fs: float, n: int, fc: float) -> float:
    if _HAS_CPP:
        return float(
            _cpp.auto_d_lowpass(
                float(fs), int(n), float(fc),
                float(_C_DEFAULT), float(_OFFSET_DEFAULT),
                float(_D_INIT), float(_D_INC), float(_D_THRESHOLD),
                int(_D_MAX_ITER), float(_D_MAX),
            )
        )
    return float(
        _fallback._auto_d_lowpass(
            float(fs), int(n), float(fc),
            c=float(_C_DEFAULT), offset=float(_OFFSET_DEFAULT),
            initial_d=float(_D_INIT), d_increment=float(_D_INC),
            threshold=float(_D_THRESHOLD), max_iter=int(_D_MAX_ITER), max_d=float(_D_MAX),
        )
    )


@lru_cache(maxsize=256)
def _auto_d_highpass(fs: float, n: int, fc: float) -> float:
    if _HAS_CPP:
        return float(
            _cpp.auto_d_highpass(
                float(fs), int(n), float(fc),
                float(_C_DEFAULT), float(_OFFSET_DEFAULT),
                float(_D_INIT), float(_D_INC), float(_D_THRESHOLD),
                int(_D_MAX_ITER), float(_D_MAX),
            )
        )
    return float(
        _fallback._auto_d_highpass(
            float(fs), int(n), float(fc),
            c=float(_C_DEFAULT), offset=float(_OFFSET_DEFAULT),
            initial_d=float(_D_INIT), d_increment=float(_D_INC),
            threshold=float(_D_THRESHOLD), max_iter=int(_D_MAX_ITER), max_d=float(_D_MAX),
        )
    )


@lru_cache(maxsize=256)
def _auto_d_bandpass(fs: float, n: int, f1: float, f2: float) -> float:
    if _HAS_CPP:
        return float(
            _cpp.auto_d_bandpass(
                float(fs), int(n), float(f1), float(f2),
                float(_C_DEFAULT), float(_OFFSET_DEFAULT),
                float(_D_INIT), float(_D_INC), float(_D_THRESHOLD),
                int(_D_MAX_ITER), float(_D_MAX),
            )
        )
    return float(
        _fallback._auto_d_bandpass(
            float(fs), int(n), float(f1), float(f2),
            c=float(_C_DEFAULT), offset=float(_OFFSET_DEFAULT),
            initial_d=float(_D_INIT), d_increment=float(_D_INC),
            threshold=float(_D_THRESHOLD), max_iter=int(_D_MAX_ITER), max_d=float(_D_MAX),
        )
    )


@lru_cache(maxsize=256)
def _gain_lowpass(fs: float, n: int, fc: float) -> np.ndarray:
    d = _auto_d_lowpass(fs, n, fc)
    if _HAS_CPP:
        g = _cpp.gain_lowpass(float(fs), int(n), float(fc),
                              float(_C_DEFAULT), float(_OFFSET_DEFAULT), float(d))
    else:
        g = _fallback.calculate_gain_lowpass(float(fs), int(n), float(fc),
                                             c=float(_C_DEFAULT), offset=float(_OFFSET_DEFAULT), d=float(d))
    g = np.ascontiguousarray(np.asarray(g, dtype=np.float64))
    g.setflags(write=False)
    return g


@lru_cache(maxsize=256)
def _gain_highpass(fs: float, n: int, fc: float) -> np.ndarray:
    d = _auto_d_highpass(fs, n, fc)
    if _HAS_CPP:
        g = _cpp.gain_highpass(float(fs), int(n), float(fc),
                               float(_C_DEFAULT), float(_OFFSET_DEFAULT), float(d))
    else:
        g = _fallback.calculate_gain_highpass(float(fs), int(n), float(fc),
                                              c=float(_C_DEFAULT), offset=float(_OFFSET_DEFAULT), d=float(d))
    g = np.ascontiguousarray(np.asarray(g, dtype=np.float64))
    g.setflags(write=False)
    return g


@lru_cache(maxsize=256)
def _gain_bandpass(fs: float, n: int, f1: float, f2: float) -> np.ndarray:
    d = _auto_d_bandpass(fs, n, f1, f2)
    if _HAS_CPP:
        g = _cpp.gain_bandpass(float(fs), int(n), float(f1), float(f2),
                               float(_C_DEFAULT), float(_OFFSET_DEFAULT), float(d))
    else:
        g = _fallback.calculate_gain_bandpass(float(fs), int(n), float(f1), float(f2),
                                              c=float(_C_DEFAULT), offset=float(_OFFSET_DEFAULT), d=float(d))
    g = np.ascontiguousarray(np.asarray(g, dtype=np.float64))
    g.setflags(write=False)
    return g


# ---------------------------------------------------------------------
# Core filtering (kept stable; used by wrappers)
# ---------------------------------------------------------------------
def lowpass(data, fs: float, fc: float, axis: int = -1):
    x = np.asarray(data, dtype=float)
    x_m = _move_axis_to_last(x, axis)
    n = int(x_m.shape[-1])

    gain = _gain_lowpass(float(fs), n, float(fc))
    X = np.ascontiguousarray(np.fft.rfft(x_m, axis=-1).astype(np.complex128, copy=False))
    Y = _apply_gain_rfft(X, gain)
    y = np.fft.irfft(Y, n=n, axis=-1)
    return _move_axis_back(y, axis)


def highpass(data, fs: float, fc: float, axis: int = -1):
    x = np.asarray(data, dtype=float)
    x_m = _move_axis_to_last(x, axis)
    n = int(x_m.shape[-1])

    gain = _gain_highpass(float(fs), n, float(fc))
    X = np.ascontiguousarray(np.fft.rfft(x_m, axis=-1).astype(np.complex128, copy=False))
    Y = _apply_gain_rfft(X, gain)
    y = np.fft.irfft(Y, n=n, axis=-1)
    return _move_axis_back(y, axis)


def bandpass(data, fs: float, f1: float, f2: float, axis: int = -1):
    if float(f2) <= float(f1):
        raise ValueError("bandpass requires f2 > f1")

    x = np.asarray(data, dtype=float)
    x_m = _move_axis_to_last(x, axis)
    n = int(x_m.shape[-1])

    gain = _gain_bandpass(float(fs), n, float(f1), float(f2))
    X = np.ascontiguousarray(np.fft.rfft(x_m, axis=-1).astype(np.complex128, copy=False))
    Y = _apply_gain_rfft(X, gain)
    y = np.fft.irfft(Y, n=n, axis=-1)
    return _move_axis_back(y, axis=axis)


# ---------------------------------------------------------------------
# SciPy-like user API (preferred)
# ---------------------------------------------------------------------
def _normalize_btype(btype: str | None) -> str:
    if btype is None:
        return "low"
    b = str(btype).strip().lower()
    if b in ("lp", "low", "lowpass", "low-pass"):
        return "low"
    if b in ("hp", "high", "highpass", "high-pass"):
        return "high"
    if b in ("bp", "band", "bandpass", "band-pass"):
        return "band"
    raise ValueError("btype must be one of: 'low', 'high', 'band' (or lowpass/highpass/bandpass aliases)")


def filter(data, fs: float, Wn=None, btype: str = "low", axis: int = -1, *,
           lowcut=None, highcut=None):
    """
    Filter data with a SciPy-like signature.

    Preferred:
        reza.filter(x, fs, Wn, btype="low|high|band")

    Backward compatibility:
        reza.filter(x, fs, lowcut=..., highcut=...)
    """
    # Legacy path (lowcut/highcut)
    if Wn is None:
        if lowcut is None and highcut is None:
            raise ValueError("Provide Wn=... (preferred) or at least one of lowcut/highcut (legacy).")
        if lowcut is not None and highcut is not None:
            return bandpass(data, fs, lowcut, highcut, axis=axis)
        if highcut is not None:
            return lowpass(data, fs, highcut, axis=axis)
        return highpass(data, fs, lowcut, axis=axis)

    bt = _normalize_btype(btype)

    if bt in ("low", "high") and isinstance(Wn, (tuple, list, np.ndarray)):
        raise ValueError("For btype='low' or 'high', Wn must be a scalar cutoff (Hz).")
    if bt == "band" and not isinstance(Wn, (tuple, list, np.ndarray)):
        raise ValueError("For btype='band', Wn must be a (low, high) tuple in Hz.")

    if bt == "low":
        return lowpass(data, fs, float(Wn), axis=axis)
    if bt == "high":
        return highpass(data, fs, float(Wn), axis=axis)

    # band
    f1, f2 = float(Wn[0]), float(Wn[1])
    return bandpass(data, fs, f1, f2, axis=axis)


# Convenience wrappers
def low(data, fs: float, fc: float, axis: int = -1):
    return lowpass(data, fs, fc, axis=axis)


def high(data, fs: float, fc: float, axis: int = -1):
    return highpass(data, fs, fc, axis=axis)


def band(data, fs: float, f1: float, f2: float, axis: int = -1):
    return bandpass(data, fs, f1, f2, axis=axis)


# Backward-compatible short aliases
def lp(data, fs: float, fc: float, axis: int = -1):
    return lowpass(data, fs, fc, axis=axis)


def hp(data, fs: float, fc: float, axis: int = -1):
    return highpass(data, fs, fc, axis=axis)


def bp(data, fs: float, f1: float, f2: float, axis: int = -1):
    return bandpass(data, fs, f1, f2, axis=axis)


# Optional capitalized aliases (do not advertise; harmless compatibility)
Low = low
High = high
Band = band


# ---------------------------------------------------------------------
# Frequency response (SciPy-like; no user-supplied n)
# ---------------------------------------------------------------------
def _next_pow2(n: int) -> int:
    if n <= 1:
        return 1
    return 1 << int(math.ceil(math.log2(n)))


def _default_n_for_freqz(fs: float, Wn, btype: str) -> int:
    fs = float(fs)

    # Determine smallest relevant cutoff (Hz)
    if btype == "band":
        fmin = min(float(Wn[0]), float(Wn[1]))
    else:
        fmin = float(Wn)

    fmin = max(fmin, 1e-6)

    # Target frequency resolution
    target_df = max(_FREQZ_MIN_DF_HZ, _FREQZ_FMIN_FRAC * fmin)

    n = int(math.ceil(fs / target_df))
    n = _next_pow2(max(_FREQZ_MIN_N, n))
    n = int(min(_FREQZ_MAX_N, n))
    return n


def freqz(*args, fs: float, worN: int = 2048, Wn=None, btype: str = "low",
          fc: float = None, f1: float = None, f2: float = None):
    """
    SciPy-like frequency response for Reza filter.

    Preferred:
        w_hz, H = reza.freqz(fs=200, Wn=5, btype="low", worN=2048)

    Backward compatibility:
        reza.freqz("lp", fs=..., fc=...)
        reza.freqz("hp", fs=..., fc=...)
        reza.freqz("bp", fs=..., f1=..., f2=...)
    """
    # Accept legacy positional "kind"
    if len(args) >= 1 and isinstance(args[0], str):
        btype = args[0]

    bt = _normalize_btype(btype)

    # Normalize cutoffs: prefer Wn, but accept legacy fc/f1/f2
    if Wn is None:
        if bt in ("low", "high"):
            if fc is None:
                raise ValueError("freqz requires Wn=... (preferred) or fc=... (legacy) for low/high.")
            Wn = float(fc)
        else:
            if f1 is None or f2 is None:
                raise ValueError("freqz requires Wn=(f1,f2) (preferred) or f1=... and f2=... (legacy) for band.")
            Wn = (float(f1), float(f2))

    fs = float(fs)
    worN = int(worN)
    if worN < 16:
        worN = 16

    n = _default_n_for_freqz(fs, Wn, bt)

    imp = np.zeros(n, dtype=float)
    imp[0] = 1.0

    if bt == "low":
        h = low(imp, fs=fs, fc=float(Wn))
    elif bt == "high":
        h = high(imp, fs=fs, fc=float(Wn))
    else:
        h = band(imp, fs=fs, f1=float(Wn[0]), f2=float(Wn[1]))

    H_full = np.fft.rfft(h)
    f_full = np.fft.rfftfreq(n, d=1.0 / fs)

    w = np.linspace(0.0, fs / 2.0, worN, endpoint=True)
    Hr = np.interp(w, f_full, H_full.real)
    Hi = np.interp(w, f_full, H_full.imag)
    return w, Hr + 1j * Hi
