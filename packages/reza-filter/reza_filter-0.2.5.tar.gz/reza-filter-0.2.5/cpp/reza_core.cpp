#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <algorithm>
#include <cmath>
#include <complex>
#include <stdexcept>
#include <vector>

namespace py = pybind11;

// Use pybind11's ssize type (portable across Windows/Linux/macOS)
using ssize = py::ssize_t;

static inline ssize rfft_len(ssize n) { return (n / 2) + 1; }

static inline std::vector<double> make_rfftfreq(ssize n, double fs) {
    if (fs <= 0.0) throw std::invalid_argument("fs must be > 0");
    if (n < 2) throw std::invalid_argument("n must be >= 2");
    const ssize m = rfft_len(n);
    std::vector<double> freqs(static_cast<size_t>(m));
    const double df = fs / static_cast<double>(n);
    for (ssize k = 0; k < m; ++k) {
        freqs[static_cast<size_t>(k)] = df * static_cast<double>(k);
    }
    return freqs;
}

static inline size_t lower_bound_idx(const std::vector<double>& a, double x) {
    auto it = std::lower_bound(a.begin(), a.end(), x);
    if (it == a.end()) return a.size() - 1;
    return static_cast<size_t>(std::distance(a.begin(), it));
}

// Matches your Python scripts:
// lowpass:  gain=1 below fc, else exp(-c*((f-fc)+offset)^d)
// highpass: gain=1 above fc, else exp(-c*((fc-f)+offset)^d)
static inline double gain_lowpass_at(double f, double fc, double c, double offset, double d) {
    if (f <= fc) return 1.0;
    return std::exp(-c * std::pow(((f - fc) + offset), d));
}

static inline double gain_highpass_at(double f, double fc, double c, double offset, double d) {
    if (f >= fc) return 1.0;
    return std::exp(-c * std::pow(((fc - f) + offset), d));
}

static py::array_t<double> gain_lowpass(double fs, ssize n, double fc, double c, double offset, double d) {
    if (fc <= 0.0) throw std::invalid_argument("fc must be > 0 for lowpass");
    auto freqs = make_rfftfreq(n, fs);
    py::array_t<double> out(static_cast<ssize>(freqs.size()));
    auto o = out.mutable_unchecked<1>();
    for (ssize i = 0; i < static_cast<ssize>(freqs.size()); ++i) {
        o(i) = gain_lowpass_at(freqs[static_cast<size_t>(i)], fc, c, offset, d);
    }
    return out;
}

static py::array_t<double> gain_highpass(double fs, ssize n, double fc, double c, double offset, double d) {
    if (fc <= 0.0) throw std::invalid_argument("fc must be > 0 for highpass");
    auto freqs = make_rfftfreq(n, fs);
    py::array_t<double> out(static_cast<ssize>(freqs.size()));
    auto o = out.mutable_unchecked<1>();
    for (ssize i = 0; i < static_cast<ssize>(freqs.size()); ++i) {
        o(i) = gain_highpass_at(freqs[static_cast<size_t>(i)], fc, c, offset, d);
    }
    return out;
}

// bandpass = highpass(fc_low) * lowpass(fc_high)
static py::array_t<double> gain_bandpass(double fs, ssize n, double fc_low, double fc_high, double c, double offset, double d) {
    if (fc_low <= 0.0 || fc_high <= 0.0) throw std::invalid_argument("cutoffs must be > 0 for bandpass");
    if (fc_low >= fc_high) throw std::invalid_argument("fc_low must be < fc_high for bandpass");

    auto freqs = make_rfftfreq(n, fs);
    py::array_t<double> out(static_cast<ssize>(freqs.size()));
    auto o = out.mutable_unchecked<1>();
    for (ssize i = 0; i < static_cast<ssize>(freqs.size()); ++i) {
        const double f = freqs[static_cast<size_t>(i)];
        o(i) = gain_highpass_at(f, fc_low, c, offset, d) * gain_lowpass_at(f, fc_high, c, offset, d);
    }
    return out;
}

// Edge-sharpness metrics follow your scripts:
// lowpass:  |g[idx]-g[idx+1]|
// highpass: |g[idx]-g[idx-1]|
// bandpass: avg( |g[i1]-g[i1-1]| , |g[i2]-g[i2+1]| )
static inline double sharpness_lowpass(const std::vector<double>& freqs, const std::vector<double>& g, double fc) {
    size_t idx = lower_bound_idx(freqs, fc);
    if (idx < 1) idx = 1;
    if (idx + 1 >= g.size()) idx = g.size() - 2;
    return std::abs(g[idx] - g[idx + 1]);
}

static inline double sharpness_highpass(const std::vector<double>& freqs, const std::vector<double>& g, double fc) {
    size_t idx = lower_bound_idx(freqs, fc);
    if (idx < 1) idx = 1;
    if (idx >= g.size() - 1) idx = g.size() - 2;
    return std::abs(g[idx] - g[idx - 1]);
}

static inline double sharpness_bandpass(const std::vector<double>& freqs, const std::vector<double>& g, double fc_low, double fc_high) {
    size_t i1 = lower_bound_idx(freqs, fc_low);
    size_t i2 = lower_bound_idx(freqs, fc_high);
    i1 = std::max<size_t>(1, std::min(i1, g.size() - 2));
    i2 = std::max<size_t>(1, std::min(i2, g.size() - 2));
    const double s1 = std::abs(g[i1] - g[i1 - 1]);
    const double s2 = std::abs(g[i2] - g[i2 + 1]);
    return 0.5 * (s1 + s2);
}

static double auto_d_lowpass(double fs, ssize n, double fc,
                            double c, double offset,
                            double initial_d, double d_increment, double threshold,
                            int max_iter, double max_d) {
    if (fc <= 0.0) throw std::invalid_argument("fc must be > 0 for lowpass");
    auto freqs = make_rfftfreq(n, fs);

    double d = initial_d;
    double last_sharp = 0.0;

    for (int it = 0; it < max_iter && d <= max_d; ++it) {
        std::vector<double> g(freqs.size());
        for (size_t i = 0; i < freqs.size(); ++i) g[i] = gain_lowpass_at(freqs[i], fc, c, offset, d);

        const double sharp = sharpness_lowpass(freqs, g, fc);
        if (std::abs(sharp - last_sharp) > threshold) {
            last_sharp = sharp;
            d += d_increment;
        } else break;
    }
    return d;
}

static double auto_d_highpass(double fs, ssize n, double fc,
                             double c, double offset,
                             double initial_d, double d_increment, double threshold,
                             int max_iter, double max_d) {
    if (fc <= 0.0) throw std::invalid_argument("fc must be > 0 for highpass");
    auto freqs = make_rfftfreq(n, fs);

    double d = initial_d;
    double last_sharp = 0.0;

    for (int it = 0; it < max_iter && d <= max_d; ++it) {
        std::vector<double> g(freqs.size());
        for (size_t i = 0; i < freqs.size(); ++i) g[i] = gain_highpass_at(freqs[i], fc, c, offset, d);

        const double sharp = sharpness_highpass(freqs, g, fc);
        if (std::abs(sharp - last_sharp) > threshold) {
            last_sharp = sharp;
            d += d_increment;
        } else break;
    }
    return d;
}

static double auto_d_bandpass(double fs, ssize n, double fc_low, double fc_high,
                             double c, double offset,
                             double initial_d, double d_increment, double threshold,
                             int max_iter, double max_d) {
    if (fc_low <= 0.0 || fc_high <= 0.0) throw std::invalid_argument("cutoffs must be > 0 for bandpass");
    if (fc_low >= fc_high) throw std::invalid_argument("fc_low must be < fc_high for bandpass");

    auto freqs = make_rfftfreq(n, fs);

    double d = initial_d;
    double last_sharp = 0.0;

    for (int it = 0; it < max_iter && d <= max_d; ++it) {
        std::vector<double> g(freqs.size());
        for (size_t i = 0; i < freqs.size(); ++i) {
            const double f = freqs[i];
            g[i] = gain_highpass_at(f, fc_low, c, offset, d) * gain_lowpass_at(f, fc_high, c, offset, d);
        }

        const double sharp = sharpness_bandpass(freqs, g, fc_low, fc_high);
        if (std::abs(sharp - last_sharp) > threshold) {
            last_sharp = sharp;
            d += d_increment;
        } else break;
    }
    return d;
}

// Multiply rFFT output by gain along last axis.
// X: complex128 array (..., nfreq)
// gain: float64 array (nfreq,)
static py::array_t<std::complex<double>> apply_gain_rfft(
    py::array_t<std::complex<double>, py::array::c_style | py::array::forcecast> X,
    py::array_t<double, py::array::c_style | py::array::forcecast> gain) {

    auto bx = X.request();
    auto bg = gain.request();

    if (bg.ndim != 1) throw std::invalid_argument("gain must be 1D");
    if (bx.ndim < 1) throw std::invalid_argument("X must have >= 1 dimension");

    const ssize ndim  = static_cast<ssize>(bx.ndim);
    const ssize nfreq = static_cast<ssize>(bx.shape[static_cast<size_t>(ndim - 1)]);
    if (bg.shape[0] != nfreq) throw std::invalid_argument("gain length must match X.shape[-1]");

    // ---- FIX (MSVC): bx.shape is a std::vector, not a pointer. Build shape safely. ----
    std::vector<ssize> shape;
    shape.reserve(static_cast<size_t>(ndim));
    for (ssize i = 0; i < ndim; ++i) {
        shape.push_back(static_cast<ssize>(bx.shape[static_cast<size_t>(i)]));
    }

    // Allocate output with the same shape as X
    py::array_t<std::complex<double>> out(shape);
    auto bo = out.request();
    // -------------------------------------------------------------------------------

    const auto* xp = static_cast<const std::complex<double>*>(bx.ptr);
    const auto* gp = static_cast<const double*>(bg.ptr);
    auto* op = static_cast<std::complex<double>*>(bo.ptr);

    const ssize total = static_cast<ssize>(bx.size);
    for (ssize i = 0; i < total; ++i) {
        const ssize k = i % nfreq;
        op[i] = xp[i] * gp[k];
    }
    return out;
}

PYBIND11_MODULE(_reza_cpp, m) {
    m.doc() = "Reza Filter C++ core (pybind11): gain templates + auto-d + rFFT multiply";

    m.def("gain_lowpass", &gain_lowpass,
          py::arg("fs"), py::arg("n"), py::arg("fc"),
          py::arg("c") = 0.9, py::arg("offset") = 1.0, py::arg("d") = 50.0);

    m.def("gain_highpass", &gain_highpass,
          py::arg("fs"), py::arg("n"), py::arg("fc"),
          py::arg("c") = 0.9, py::arg("offset") = 1.0, py::arg("d") = 50.0);

    m.def("gain_bandpass", &gain_bandpass,
          py::arg("fs"), py::arg("n"), py::arg("fc_low"), py::arg("fc_high"),
          py::arg("c") = 0.9, py::arg("offset") = 1.0, py::arg("d") = 50.0);

    m.def("auto_d_lowpass", &auto_d_lowpass,
          py::arg("fs"), py::arg("n"), py::arg("fc"),
          py::arg("c") = 0.9, py::arg("offset") = 1.0,
          py::arg("initial_d") = 10.0, py::arg("d_increment") = 5.0, py::arg("threshold") = 1e-4,
          py::arg("max_iter") = 200, py::arg("max_d") = 1e6);

    m.def("auto_d_highpass", &auto_d_highpass,
          py::arg("fs"), py::arg("n"), py::arg("fc"),
          py::arg("c") = 0.9, py::arg("offset") = 1.0,
          py::arg("initial_d") = 10.0, py::arg("d_increment") = 5.0, py::arg("threshold") = 1e-4,
          py::arg("max_iter") = 200, py::arg("max_d") = 1e6);

    m.def("auto_d_bandpass", &auto_d_bandpass,
          py::arg("fs"), py::arg("n"), py::arg("fc_low"), py::arg("fc_high"),
          py::arg("c") = 0.9, py::arg("offset") = 1.0,
          py::arg("initial_d") = 10.0, py::arg("d_increment") = 5.0, py::arg("threshold") = 1e-4,
          py::arg("max_iter") = 200, py::arg("max_d") = 1e6);

    m.def("apply_gain_rfft", &apply_gain_rfft, py::arg("X"), py::arg("gain"));
}
