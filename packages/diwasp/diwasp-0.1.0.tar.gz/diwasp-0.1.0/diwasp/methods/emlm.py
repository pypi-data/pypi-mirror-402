"""Extended Maximum Likelihood Method (EMLM) for directional spectrum estimation.

The EMLM inverts the cross-spectral density matrix to estimate the directional
spectrum with improved resolution compared to DFTM.

Reference:
    Hashimoto, N. (1997) "Analysis of the directional wave spectrum from
    field data" in Advances in Coastal Engineering Vol. 3, World Scientific.
"""

import numpy as np
from numpy.typing import NDArray

from .base import EstimationMethodBase


class EMLM(EstimationMethodBase):
    """Extended Maximum Likelihood Method.

    The EMLM estimates the directional spectrum using matrix inversion:

    E(theta) = 1 / sum_nm [H_n * H_m* * C_inv_nm * exp(i * kx_nm)]

    This method provides better directional resolution than DFTM but is
    more sensitive to noise due to the matrix inversion.
    """

    def estimate(
        self,
        csd_matrix: NDArray[np.complexfloating],
        transfer_matrix: NDArray[np.complexfloating],
        kx: NDArray[np.floating],
    ) -> NDArray[np.floating]:
        """Estimate directional spectrum using EMLM.

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
            # Invert CSD matrix
            try:
                invcps = np.linalg.inv(csd_matrix[ff])
            except np.linalg.LinAlgError:
                invcps = np.linalg.pinv(csd_matrix[ff])

            # Fully vectorized computation using broadcasting and einsum
            H = transfer_matrix[ff, :, :]  # [n_dirs x n_sensors]
            Hs = np.conj(transfer_matrix[ff, :, :])  # [n_dirs x n_sensors]

            # Phase differences: [n_dirs x n_sensors x n_sensors]
            kx_ff = kx[ff, :, :]  # [n_dirs x n_sensors]
            phase_diff = kx_ff[:, :, np.newaxis] - kx_ff[:, np.newaxis, :]
            expx = np.exp(1j * phase_diff)

            # Htemp[d, m, n] = H[d, n] * Hs[d, m] * expx[d, m, n]
            Htemp = H[:, np.newaxis, :] * Hs[:, :, np.newaxis] * expx

            # Sftmp[d] = sum_mn invcps[m,n] * Htemp[d,m,n]
            Sftmp = np.einsum("mn,dmn->d", invcps, Htemp)

            # EMLM: E = 1 / Sftmp
            E = 1.0 / np.maximum(np.real(Sftmp), 1e-20)

            # Normalize to sum=1 (directional distribution)
            total = np.sum(E)
            if total > 0:
                E = E / total

            S[ff, :] = E

        return S
