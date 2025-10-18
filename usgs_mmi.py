# usgs_mmi.py
# Modified from shindo.py by RR-Inyo (https://github.com/RR-Inyo/seismopi, https://github.com/RR-Inyo/shindo)
# Copyright (c) 2021 RR-Inyo (assumed, based on original repository)
# Modifications for USGS Modified Mercalli Intensity (MMI) by Grok, created for personal use or with permission.
# Calculates MMI from 3-axis acceleration data using PGA-based regression.

import numpy as np

def get_mmi(accel, sample_rate=100):
    """
    Calculate USGS Modified Mercalli Intensity from acceleration data.
    accel: NumPy array of shape (n_samples, 3) with x, y, z accelerations in gal (cm/s^2)
    sample_rate: Sampling rate in Hz (default 100 Hz for 10 ms intervals)
    Returns: Float MMI value (e.g., 5.2)
    """
    # Compute Peak Ground Acceleration (PGA)
    # Vector magnitude: sqrt(x^2 + y^2 + z^2) for each sample
    magnitudes = np.sqrt(np.sum(accel**2, axis=1))
    pga = np.max(magnitudes)  # PGA in gal (cm/s^2)

    # USGS MMI regression: MMI = 3.93 * log10(PGA) - 1.17 (PGA in cm/s^2)
    if pga <= 0:
        return 0.0  # Avoid log(0)
    mmi = 3.93 * np.log10(pga) - 1.17

    # Clamp to realistic MMI range (I to XII, typically 1 to 10 for instrumental)
    return max(1.0, min(10.0, mmi))