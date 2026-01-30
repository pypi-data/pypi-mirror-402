"""Direct Fourier Transform Method (DFTM) for directional spectrum estimation.

The DFTM is the simplest directional estimation method. It directly integrates
the cross-spectra with transfer functions without iteration.

Reference:
    Hashimoto, N. (1997) "Analysis of the directional wave spectrum from
    field data" in Advances in Coastal Engineering Vol. 3, World Scientific.
"""

import numpy as np
from numpy.typing import NDArray

from .base import EstimationMethodBase


class DFTM(EstimationMethodBase):
    """Direct Fourier Transform Method.

    The DFTM estimates the directional spectrum through direct integration:

    S(f, theta) ~ sum_n sum_m [H_n * H_m* * C_nm * exp(i * kx_nm)]

    This is a non-iterative method that provides quick estimates but may
    produce spectra with negative values due to noise.
    """

    def estimate(
        self,
        csd_matrix: NDArray[np.complexfloating],
        transfer_matrix: NDArray[np.complexfloating],
        kx: NDArray[np.floating],
    ) -> NDArray[np.floating]:
        """Estimate directional spectrum using DFTM.

        Args:
            csd_matrix: Cross-spectral density matrix [n_freqs x n_sensors x n_sensors].
            transfer_matrix: Transfer functions [n_freqs x n_dirs x n_sensors].
            kx: Spatial phase lags [n_freqs x n_dirs x n_sensors].

        Returns:
            Directional spectrum estimate [n_freqs x n_dirs].
        """
        n_freqs, n_dirs, n_sensors = transfer_matrix.shape
        ddir = 2.0 * np.pi / n_dirs

        # Initialize output spectrum
        S = np.zeros((n_freqs, n_dirs))

        for ff in range(n_freqs):
            # Fully vectorized computation using broadcasting and einsum
            # H[n_dirs, n_sensors]
            H = transfer_matrix[ff, :, :]  # [n_dirs x n_sensors]
            Hs = np.conj(transfer_matrix[ff, :, :])  # [n_dirs x n_sensors]

            # Phase differences: [n_dirs x n_sensors x n_sensors]
            kx_ff = kx[ff, :, :]  # [n_dirs x n_sensors]
            phase_diff = kx_ff[:, :, np.newaxis] - kx_ff[:, np.newaxis, :]
            expx = np.exp(1j * phase_diff)

            # Htemp[d, m, n] = H[d, n] * Hs[d, m] * expx[d, m, n]
            Htemp = H[:, np.newaxis, :] * Hs[:, :, np.newaxis] * expx

            # Sftmp[d] = sum_mn C[m,n] * Htemp[d,m,n]
            Sftmp = np.einsum("mn,dmn->d", csd_matrix[ff], Htemp)

            # Take real part and ensure non-negative
            E = np.real(Sftmp)
            E = np.maximum(E, 0.0)

            # Normalize to unit directional distribution
            # Note: The actual energy scaling is handled by the calling function
            total = np.sum(E)
            if total > 0:
                E = E / total

            S[ff, :] = E

        return S
