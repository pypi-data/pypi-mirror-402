import numpy as np
import reza

def test_import():
    assert hasattr(reza, "bandpass")

def test_bandpass_shape():
    fs = 100.0
    t = np.arange(0, 2, 1/fs)
    x = np.sin(2*np.pi*1.0*t) + 0.2*np.sin(2*np.pi*30.0*t)
    y = reza.bandpass(x, fs, 0.5, 5.0)
    assert y.shape == x.shape
