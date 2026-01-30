from __future__ import annotations
import numpy as np
from dataclasses import dataclass

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any, TypeAlias, Sequence
    from numpy.typing import NDArray

    _DictKey: TypeAlias = str | int | tuple["_DictKey", ...]


def normalize_result_axis(
    axis: tuple[int, ...] | int | None,
    result: NDArray[Any],
    ell: Sequence[Any] | NDArray[Any] | None,
) -> tuple[int, ...]:
    """
    Normalize the axis argument for result arrays.

    Returns a tuple of axis indices, handling None and negative values.
    """
    try:
        from numpy.lib.array_utils import normalize_axis_tuple
    except ModuleNotFoundError:
        from numpy.lib.stride_tricks import normalize_axis_tuple  # type: ignore

    if axis is None:
        if result.ndim == 0:
            axis = ()
        elif isinstance(ell, tuple):
            axis = tuple(range(-len(ell), 0))
        else:
            axis = -1
    return normalize_axis_tuple(axis, result.ndim, "axis")


@dataclass(frozen=True, repr=False)
class AngularPowerSpectrum:
    """
    AngularPowerSpectrum: A sleek dataclass for LSS numerical results and metadata.
    for angular power spectra and mixing matrix results.

    Attributes:
        array: Main power spectrum data (float dtype).
        ell: Multipole moment(s) or bin centers.
        axis: Axis or axes corresponding to result dimensions.
        lower: Optional lower error bounds.
        upper: Optional upper error bounds.
        weight: Optional weights (e.g. mode counts or covariance weights).
        software: Optional software identifier.
    """

    array: NDArray[Any]
    ell: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    axis: int | tuple[int, ...] | None = None
    lower: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    upper: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    weight: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    software: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        float_array = np.asarray(self.array, dtype=float)
        object.__setattr__(self, "array", float_array)
        axis = normalize_result_axis(self.axis, self.array, self.ell)
        object.__setattr__(self, "axis", axis)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(axis={self.axis!r})"

    def __array__(
        self,
        dtype: np.dtype[Any] | None = None,
        *,
        copy: bool | None = None,
    ) -> NDArray[Any]:
        if copy is not None:
            return self.array.__array__(dtype, copy=copy)
        return self.array.__array__(dtype)

    def __getitem__(self, key: Any) -> Any:
        return self.array[key]

    @property
    def ndim(self) -> int:
        return self.array.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        return self.array.shape

    @property
    def dtype(self) -> np.dtype[Any]:
        return self.array.dtype


@dataclass(frozen=True, repr=False)
class TwoPointCorrelationFunction:
    """
    TwoPointCorrelationFunction: Dataclass for 2PCF results and metadata.

    Attributes:
        array: Main correlation data (float dtype).
        theta: Angular separation(s) or bin centers.
        axis: Axis or axes corresponding to result dimensions.
        lower: Optional lower error bounds.
        upper: Optional upper error bounds.
        weight: Optional weights (e.g. pair counts or covariance weights).
        software: Optional software identifier.
    """

    array: NDArray[Any]
    theta: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    axis: int | tuple[int, ...] | None = None
    lower: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    upper: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    weight: NDArray[Any] | tuple[NDArray[Any], ...] | None = None
    software: str | None = None

    def __post_init__(self) -> None:
        float_array = np.asarray(self.array, dtype=float)
        object.__setattr__(self, "array", float_array)
        axis = normalize_result_axis(self.axis, self.array, self.theta)
        object.__setattr__(self, "axis", axis)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(axis={self.axis!r})"

    def __array__(
        self,
        dtype: np.dtype[Any] | None = None,
        *,
        copy: bool | None = None,
    ) -> NDArray[Any]:
        if copy is not None:
            return self.array.__array__(dtype, copy=copy)
        return self.array.__array__(dtype)

    def __getitem__(self, key: Any) -> Any:
        return self.array[key]

    @property
    def ndim(self) -> int:
        return self.array.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        return self.array.shape

    @property
    def dtype(self) -> np.dtype[Any]:
        return self.array.dtype


@dataclass(frozen=True, repr=False)
class COSEBI:
    """
    AngularPowerSpectrum: A sleek dataclass for LSS numerical results and metadata.
    for angular power spectra and mixing matrix results.

    Attributes:
        array: Main power spectrum data (float dtype).
        axis: Axis or axes corresponding to result dimensions.
        mode: Multipole moment(s) or bin centers.
        nmode: Optional number of modes per bin
        thmin: Optional minimum angular scale.
        thmax: Optional maximum angular scale.
        software: Optional software identifier.
    """

    array: NDArray[Any]
    axis: int | tuple[int, ...] | None = None
    mode: int | tuple[int, ...] | None = None
    nmodes: int | tuple[int, ...] | None = None
    thmin: float | None = None
    thmax: float | None = None
    software: str | None = None

    def __post_init__(self) -> None:
        float_array = np.asarray(self.array, dtype=float)
        object.__setattr__(self, "array", float_array)
        axis = normalize_result_axis(self.axis, self.array, self.mode)
        object.__setattr__(self, "axis", axis)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(axis={self.axis!r})"

    def __array__(
        self,
        dtype: np.dtype[Any] | None = None,
        *,
        copy: bool | None = None,
    ) -> NDArray[Any]:
        if copy is not None:
            return self.array.__array__(dtype, copy=copy)
        return self.array.__array__(dtype)

    def __getitem__(self, key: Any) -> Any:
        return self.array[key]

    @property
    def ndim(self) -> int:
        return self.array.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        return self.array.shape

    @property
    def dtype(self) -> np.dtype[Any]:
        return self.array.dtype
