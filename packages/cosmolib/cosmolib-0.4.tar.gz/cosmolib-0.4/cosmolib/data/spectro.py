from __future__ import annotations
from dataclasses import dataclass

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any
    from numpy.typing import NDArray


@dataclass(frozen=True)
class PowerSpectrum:
    """
    Output datamodel for read LE3 GC PK measurements, containing information on the header and the power spectrum multipoles.

    Attributes
    ----------
    k : ndarray
        centers of k bins
    k_eff : ndarray
        effective values of k bins
    mode_number : ndarray
        number of modes in each k bin
    p : dict[ndarray]
        multipoles of the power spectrum (keys are integer l's from 0 to 4)
    fiducial_cosmology : dict[str, float]
        Fiducial cosmology used in the measurement
    redshift_eff : ndarray
        Effective redshift of the measurement
    shot_noise : float
        Value of shot noise
    number_density : float
        Number density of galaxies used in the measurement
    shot_noise : float
        Value of shot noise
    """

    k: NDArray[Any]
    k_eff: NDArray[Any]
    mode_number: NDArray[Any]
    p: NDArray[Any]
    fiducial_cosmology: dict[str, float]  # Fiducial cosmology used in the measurement
    redshift_eff: NDArray[Any]  # Effective redshift of the measurement
    number_density: float  # Number density of galaxies used in the measurement
    shot_noise: float  # Value of shot noise

    def __post_init__(self) -> None:
        # Sanity check on the attributes
        if any(
            [
                len(self.k) != len(self.k_eff),
                len(self.k) != len(self.mode_number),
            ]
        ):
            raise ValueError(
                "Inconsistent class attributes, all arrays must have the same length."
            )

    def __len__(self) -> int:
        return len(self.k)
