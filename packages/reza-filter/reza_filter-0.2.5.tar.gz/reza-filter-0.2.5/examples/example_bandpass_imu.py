import numpy as np
import reza

fs = 100.0
t = np.arange(0, 10, 1/fs)
x = np.sin(2*np.pi*1.2*t) + 0.3*np.sin(2*np.pi*20*t) + 0.05*np.random.randn(t.size)

y = reza.bandpass(x, fs, 0.5, 5.0)
print("done", y.shape, "has_cpp=", reza.has_cpp())
